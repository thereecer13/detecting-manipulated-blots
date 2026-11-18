"""Fast scan for solid copied blocks in a tissue image (clone-stamp retouching large enough to matter).

Rule (from the reviewer's labels): a copy is a continuous block of exactly matching pixels, with stained
texture inside, whose surroundings do not match at the same offset. Patchy matches, pale background and
periodic tissue are not copies.

1. Candidates: 9x9 gray patches indexed on a 2 px grid; textured query patches on a QG px grid, at all
   four pixel parities, look up their nearest neighbours. Near-identical pairs MIN_DIST-MAX_DIST px apart
   vote for an offset; offsets with >= MIN_VOTES votes inside one neighbourhood are kept.
2. Verification at each offset: pixels where the colour image equals itself shifted (max channel
   difference <= TOL), textured and not pale; opened with a KxK square; the largest remaining block must
   reach BLOCK_MIN px and the ring around it must differ (mean difference >= RING_RATIO x inside).

    python3 block_clone.py scan index.jsonl images_dir --out hits.json [--jobs 3] [--skip N]
"""
import argparse, json, sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2, numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent.parent))
from copy_move import fit, mask_watermark

P, QG, K = 9, 6, 6
MIN_DIST, MAX_DIST = 16, 200
PATCH_NCC, MIN_STD = 0.97, 6.0
MIN_VOTES, CELL = 3, 32
TOL, OPEN, BLOCK_MIN, RING_RATIO, PALE = 14, 11, 120, 2.0, 225


def candidates(g, valid):
    win = np.lib.stride_tricks.sliding_window_view(g, (P, P)); H, W = win.shape[:2]
    def feats(ys, xs):
        f = win[ys, xs].reshape(len(ys), -1).astype(np.float32); f -= f.mean(1, keepdims=True)
        n = np.linalg.norm(f, axis=1); return f / np.maximum(n, 1e-6)[:, None], n / P
    sd = cv2.GaussianBlur(g * g, (P, P), 0) - cv2.GaussianBlur(g, (P, P), 0) ** 2
    ok = (np.sqrt(np.maximum(sd, 0)) >= MIN_STD) & valid & (cv2.GaussianBlur(g, (P, P), 0) < PALE)
    ok = ok[P // 2:P // 2 + H, P // 2:P // 2 + W]
    iy, ix = np.mgrid[0:H:2, 0:W:2]; m = ok[iy, ix]; iy, ix = iy[m], ix[m]
    if len(iy) < 50: return []
    fi, _ = feats(iy, ix); index = cv2.flann_Index(fi, dict(algorithm=1, trees=4)); votes = defaultdict(set)
    for py in (0, 1):
        for px in (0, 1):
            qy, qx = np.mgrid[py:H:QG, px:W:QG]; m = ok[qy, qx]; qy, qx = qy[m], qx[m]
            if not len(qy): continue
            fq, _ = feats(qy, qx); nn, _ = index.knnSearch(fq, K, params=dict(checks=48))
            for k in range(K):
                j = nn[:, k]; c = (fq * fi[j]).sum(1); dx, dy = ix[j] - qx, iy[j] - qy; d = np.hypot(dx, dy)
                for i in np.where((c >= PATCH_NCC) & (d >= MIN_DIST) & (d <= MAX_DIST))[0]:
                    ax, ay, ddx, ddy = int(qx[i]), int(qy[i]), int(dx[i]), int(dy[i])
                    if (ddx, ddy) < (0, 0): ax, ay, ddx, ddy = ax + ddx, ay + ddy, -ddx, -ddy
                    votes[(ddx, ddy)].add((ax, ay))
    out = []
    for (dx, dy), pts in votes.items():
        if len(pts) < MIN_VOTES: continue
        cells = defaultdict(int)
        for x, y in pts: cells[(x // CELL, y // CELL)] += 1
        best = max(sum(cells.get((cx + a, cy + b), 0) for a in (-1, 0, 1) for b in (-1, 0, 1)) for cx, cy in cells)
        if best >= MIN_VOTES: out.append((best, dx, dy))
    out.sort(reverse=True)
    return out[:60]


def verify(rgb, g, valid, cand):
    h, w = g.shape; im = rgb.astype(np.int16); res = []
    tex = np.sqrt(np.maximum(cv2.GaussianBlur(g * g, (0, 0), 2) - cv2.GaussianBlur(g, (0, 0), 2) ** 2, 0))
    base = (tex >= 4) & valid & (cv2.GaussianBlur(g, (0, 0), 2) < PALE)
    for v, dx, dy in cand:
        ys, xs = slice(max(0, -dy), min(h, h - dy)), slice(max(0, -dx), min(w, w - dx))
        yt, xt = slice(max(0, dy), min(h, h + dy)), slice(max(0, dx), min(w, w + dx))
        df = np.abs(im[ys, xs] - im[yt, xt]).max(2)
        m = ((df <= TOL) & base[ys, xs] & base[yt, xt]).astype(np.uint8)
        o = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((OPEN, OPEN), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(o)
        for k in range(1, n):
            a = int(st[k, cv2.CC_STAT_AREA])
            if a < BLOCK_MIN: continue
            x, y, bw, bh = (int(t) for t in st[k, :4]); p = 24
            y0, y1, x0, x1 = max(0, y - p), min(df.shape[0], y + bh + p), max(0, x - p), min(df.shape[1], x + bw + p)
            blk = (lab[y0:y1, x0:x1] == k).astype(np.uint8); d = df[y0:y1, x0:x1]
            ring = cv2.dilate(blk, np.ones((41, 41), np.uint8)) - cv2.dilate(blk, np.ones((9, 9), np.uint8))
            ins, out = float(d[blk > 0].mean()), float(d[ring > 0].mean()) if ring.any() else 0.0
            if out < RING_RATIO * max(ins, 1) or out < 15: continue
            cnt, _ = cv2.findContours(blk, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ox, oy = xs.start + x0, ys.start + y0
            poly = [[int(ox + q[0][0]), int(oy + q[0][1])] for q in max(cnt, key=cv2.contourArea)]
            res.append({"area": a, "votes": int(v), "shift": [int(dx), int(dy)], "inside": round(ins, 1), "ring": round(out, 1),
                        "bbox": [xs.start + x, ys.start + y, bw, bh], "outline": poly})
    res.sort(key=lambda r: -r["area"]); keep = []
    for r in res:      # one entry per place: drop blocks overlapping a larger kept one (either end)
        bx, by, bw, bh = r["bbox"]; ends = [(bx, by), (bx + r["shift"][0], by + r["shift"][1])]
        def near(q):
            qx, qy, qw, qh = q["bbox"]; qe = [(qx, qy), (qx + q["shift"][0], qy + q["shift"][1])]
            return any(abs(a - c) < max(bw, qw) and abs(b - d) < max(bh, qh) for a, b in ends for c, d in qe)
        if not any(near(q) for q in keep): keep.append(r)
    return keep


def detect(rgb):
    rgb = fit(rgb); g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32); valid = mask_watermark(*g.shape) > 0
    return verify(rgb, g, valid, candidates(g, valid))


def _scan(path):
    try: return detect(np.asarray(Image.open(path).convert("RGB")))
    except Exception as e: return {"error": str(e)[:80]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["scan"]); ap.add_argument("index"); ap.add_argument("images")
    ap.add_argument("--out", required=True); ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(); rows = [json.loads(l) for l in open(a.index) if l.strip()][a.skip:]; seen = set(); rows = [r for r in rows if not (r["file"] in seen or seen.add(r["file"]))]
    done = {}
    if Path(a.out).exists(): done = {r["file"]: r for r in json.load(open(a.out))}
    todo = [r for r in rows if r["file"] not in done]
    with ProcessPoolExecutor(a.jobs) as ex:
        for i, (r, f) in enumerate(zip(todo, ex.map(_scan, [f"{a.images}/{r['file']}" for r in todo], chunksize=2))):
            r["found"] = f; done[r["file"]] = r
            if i % 25 == 24 or i == len(todo) - 1: json.dump(list(done.values()), open(a.out, "w")); print(i + 1, "/", len(todo), flush=True)
    hits = [r for r in done.values() if isinstance(r["found"], list) and r["found"]]
    print(len(done), "images,", len(hits), "with a solid copied block")

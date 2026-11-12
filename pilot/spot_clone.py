"""Find small cloned spots ("spot cleaning", clone-stamp retouching) inside one tissue image.

1. Candidates: every 7x7 gray patch with texture (std >= MIN_STD) is indexed at every pixel position;
   patches on a STEP-px grid query their K nearest neighbours (FLANN KD-tree). Pairs that are nearly
   identical (patch NCC >= PATCH_NCC) and MIN_DIST-MAX_DIST px apart vote for (offset, location cell).
   A cloned spot gives a compact cluster of votes with one offset. (Indexing every position matters:
   with both sides on a 2 px grid, only copies with an even offset in x and y could be found.)
2. Verification at each candidate offset, around its cell: local NCC of the image with itself shifted
   (> 0.9), of the fine-noise residuals (> 0.7), texture, and a peak test: the match must be better at
   this offset than 3 px away in all 8 directions (edges and smooth structures match along themselves).
   Area = largest connected region that passes.

Synthetic test (soft-brush clone-stamp spots of 14-34 px, offsets <= 120 px, JPEG q85, Proteintech IHC
images; scratchpad sc_synth): with the true offset given, 95/109 spots pass verification and 0 of
15,931 random offsets in clean images reach area 40. End to end at area >= 60: 28/57 spots found, 2/30
clean images with an alarm. Slow: ~2 min per image per core.

    python pilot/spot_clone.py scan index.jsonl images_dir --out hits.json [--jobs 3]
    python pilot/spot_clone.py show image.jpg out.png
    python pilot/spot_clone.py synth images_dir out_dir --n 200
    python pilot/spot_clone.py validate synth_dir [--n 30]
"""
import argparse, json, random, sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from copy_move import fit, mask_watermark, _local_ncc

P, STEP, K = 7, 2, 16
MIN_DIST, MAX_DIST = 12, 160
PATCH_NCC = 0.95
MIN_STD = 5.0
MIN_VOTES, CELL = 4, 24
PEAK = 0.08
AREA_MIN = 60


def _patches(g):
    win = np.lib.stride_tricks.sliding_window_view(g, (P, P))
    ys, xs = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    f = win.reshape(-1, P * P).astype(np.float32); f = f - f.mean(1, keepdims=True)
    return f, np.linalg.norm(f, axis=1), f.std(1), xs.ravel(), ys.ravel()


def candidates(g, valid):
    f, n, sd, xs, ys = _patches(g)
    ok = (sd >= MIN_STD) & valid[ys + P // 2, xs + P // 2]
    f, xs, ys = f[ok] / n[ok][:, None], xs[ok], ys[ok]
    q = (xs % STEP == 0) & (ys % STEP == 0); fq, xq, yq = f[q], xs[q], ys[q]
    if len(fq) < 10: return []
    nn, _ = cv2.flann_Index(f, dict(algorithm=1, trees=4)).knnSearch(fq, K, params=dict(checks=64))
    votes = defaultdict(set)
    for k in range(K):
        j = nn[:, k]; good = j >= 0; jj = np.where(good, j, 0)
        c = (fq * f[jj]).sum(1); dx, dy = xs[jj] - xq, ys[jj] - yq; d = np.hypot(dx, dy)
        for i in np.where(good & (c >= PATCH_NCC) & (d >= MIN_DIST) & (d <= MAX_DIST))[0]:
            ax, ay, ddx, ddy = int(xq[i]), int(yq[i]), int(dx[i]), int(dy[i])
            if (ddx, ddy) < (0, 0): ax, ay, ddx, ddy = ax + ddx, ay + ddy, -ddx, -ddy     # canonical direction
            votes[(ddx, ddy, ax // CELL, ay // CELL)].add((ax, ay))
    out = []
    for (dx, dy, cx, cy) in votes:
        tot = set()
        for ex in (-1, 0, 1):
            for ey in (-1, 0, 1):
                for ccx in (-1, 0, 1):
                    for ccy in (-1, 0, 1): tot |= votes.get((dx + ex, dy + ey, cx + ccx, cy + ccy), set())
        if len(tot) >= MIN_VOTES: out.append((len(tot), dx, dy, cx, cy))
    out.sort(reverse=True); keep = []
    for v, dx, dy, cx, cy in out:
        if any(abs(dx - a) <= 2 and abs(dy - b) <= 2 and abs(cx - c) <= 1 and abs(cy - d) <= 1 for _, a, b, c, d in keep): continue
        keep.append((v, dx, dy, cx, cy))
    return keep[:40]


def verify(g, cand):
    h, w = g.shape; rr = g - cv2.GaussianBlur(g, (0, 0), 1.0); res = []
    for v, dx, dy, cx, cy in cand:
        x0, y0 = max(0, cx * CELL - CELL), max(0, cy * CELL - CELL)
        x1, y1 = min(w, cx * CELL + 2 * CELL + P), min(h, cy * CELL + 2 * CELL + P)
        if not (0 <= x0 + dx - 3 and x1 + dx + 3 <= w and 0 <= y0 + dy - 3 and y1 + dy + 3 <= h): continue
        A, B = g[y0:y1, x0:x1], g[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
        nc, sd = _local_ncc(A, B, win=7)
        nr, _ = _local_ncc(rr[y0:y1, x0:x1], rr[y0 + dy:y1 + dy, x0 + dx:x1 + dx], win=7)
        alt = np.full_like(nc, -1)
        for ex, ey in ((3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, -2), (2, -2), (-2, 2)):
            alt = np.maximum(alt, _local_ncc(A, g[y0 + dy + ey:y1 + dy + ey, x0 + dx + ex:x1 + dx + ex], win=7)[0])
        reg = (nc > 0.9) & (nr > 0.7) & (sd > MIN_STD) & (nc - alt > PEAK)
        reg = cv2.morphologyEx(reg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        n, _, st, _ = cv2.connectedComponentsWithStats(reg)
        if n < 2: continue
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        res.append({"area": int(st[k, cv2.CC_STAT_AREA]), "votes": v, "shift": [dx, dy],
                    "bbox": [int(x0 + st[k, 0]), int(y0 + st[k, 1]), int(st[k, 2]), int(st[k, 3])]})
    res.sort(key=lambda r: -r["area"]); return res


def detect(rgb):
    rgb = fit(rgb); g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return verify(g, candidates(g, mask_watermark(*g.shape) > 0))


def overlay(rgb, found, path):
    im = fit(rgb).copy()
    for d, c in zip(found[:3], ((255, 140, 0), (0, 160, 255), (220, 0, 220))):
        x, y, bw, bh = d["bbox"]; dx, dy = d["shift"]
        for ox, oy in ((0, 0), (dx, dy)): cv2.rectangle(im, (x + ox - 4, y + oy - 4), (x + ox + bw + 4, y + oy + bh + 4), c, 2)
    Image.fromarray(im).save(path)


def _scan(path):
    try: rgb = np.asarray(Image.open(path).convert("RGB"))
    except Exception as e: return {"error": str(e)[:80]}
    f = detect(rgb)
    return {"area": f[0]["area"] if f else 0, "found": f[:5]}


def synth(src_dir, out_dir, n, seed=7):
    rng = random.Random(seed); files = sorted(Path(src_dir).glob("*.jpg")); rng.shuffle(files)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True); meta = []
    for f in files[:n]:
        rgb = fit(np.asarray(Image.open(f).convert("RGB"))).copy(); h, w = rgb.shape[:2]
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        s = rng.randint(14, 34); fake = rgb.astype(np.float32).copy(); spots = []
        for _ in range(rng.randint(1, 3)):
            for _ in range(100):
                x0, y0 = rng.randint(0, w - s - 1), rng.randint(0, int(0.85 * h) - s - 1)
                dx, dy = rng.randint(-120, 120), rng.randint(-120, 120); x1, y1 = x0 + dx, y0 + dy
                if np.hypot(dx, dy) >= 20 and 0 <= x1 < w - s and 0 <= y1 < int(0.85 * h) - s and g[y0:y0 + s, x0:x0 + s].std() > 12: break
            yy, xx = np.mgrid[:s, :s]; r = np.hypot(yy - s / 2, xx - s / 2) / (s / 2)
            alpha = np.clip(1.4 - r, 0, 1)[..., None]                   # soft brush: hard centre, feathered edge
            spots.append([x0, y0, dx, dy])
            fake[y1:y1 + s, x1:x1 + s] = alpha * rgb[y0:y0 + s, x0:x0 + s] + (1 - alpha) * fake[y1:y1 + s, x1:x1 + s]
        Image.fromarray(np.clip(fake, 0, 255).astype(np.uint8)).save(out / f"pos_{f.stem}.jpg", quality=85)
        Image.fromarray(rgb).save(out / f"neg_{f.stem}.jpg", quality=85)
        meta.append({"file": f"pos_{f.stem}.jpg", "size": s, "spots": spots}); meta.append({"file": f"neg_{f.stem}.jpg"})
    (out / "meta.json").write_text(json.dumps(meta, indent=1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["scan", "show", "synth", "validate"])
    ap.add_argument("a"); ap.add_argument("b", nargs="?"); ap.add_argument("--out", type=Path)
    ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    if a.mode == "show":
        rgb = np.asarray(Image.open(a.a).convert("RGB")); f = detect(rgb); overlay(rgb, f, a.b)
        for d in f[:5]: print(d)
    elif a.mode == "synth": synth(a.a, a.b, a.n)
    elif a.mode == "validate":
        d = Path(a.a); meta = json.loads((d / "meta.json").read_text())
        pos = [m for m in meta if m["file"].startswith("pos")][:a.n]; neg = [m for m in meta if m["file"].startswith("neg")][:a.n]
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [str(d / m["file"]) for m in pos + neg]))
        rp, rn = res[:len(pos)], res[len(pos):]
        for thr in (30, AREA_MIN, 100):
            spots = hit = 0
            for m, r in zip(pos, rp):
                for (x0, y0, dx, dy) in m["spots"]:
                    spots += 1
                    hit += any(c["area"] >= thr and abs(abs(c["shift"][0]) - abs(dx)) <= 2 and abs(abs(c["shift"][1]) - abs(dy)) <= 2 for c in r.get("found", []))
            print(f"area >= {thr}: spots found {hit}/{spots}; clean images with an alarm {sum(r.get('area', 0) >= thr for r in rn)}/{len(rn)}")
    else:
        recs = [json.loads(l) for l in Path(a.a).read_text().splitlines()]
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [str(Path(a.b) / r["file"]) for r in recs], chunksize=2))
        out = [{**r, **x} for r, x in zip(recs, res)]; a.out.write_text(json.dumps(out, indent=1))
        hits = sorted([o for o in out if o.get("area", 0) >= AREA_MIN], key=lambda o: -o["area"])
        print(f"{len(out)} images, {len(hits)} with a verified cloned spot (area >= {AREA_MIN})")
        for o in hits[:40]: print(o["area"], o["found"][0]["shift"], o["catalog"], o.get("image_url", "").split("/")[-1])


if __name__ == "__main__":
    main()

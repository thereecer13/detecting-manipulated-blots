"""Find small cloned spots ("spot cleaning", clone-stamp retouching) inside one tissue image.

Dense block matching (after Fridrich et al. 2003): every BxB block on a STEP-px grid gets a feature
vector (4x4 grid of local means, block mean removed), blocks are sorted lexicographically by their
quantized features, and neighbours in that order that are nearly identical but at least MIN_DIST px
apart are pairs of similar blocks. A cloned spot produces many such pairs with the same shift vector;
natural texture produces scattered shifts. Shift vectors with at least MIN_BLOCKS pairs are then
verified pixel by pixel (local correlation of the image with itself shifted, textured areas only).
Flat areas (white lumen, background) are excluded because they match everywhere.

    python pilot/spot_clone.py scan index.jsonl images_dir --out hits.json
    python pilot/spot_clone.py show image.jpg out.png
    python pilot/spot_clone.py synth images_dir out_dir --n 200     (soft-edged clone-stamp spots)
    python pilot/spot_clone.py validate synth_dir
"""
import argparse, json, random, sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from copy_move import fit, mask_watermark, _local_ncc

B, STEP = 8, 2
MIN_DIST = 14
K = 8                 # nearest neighbours compared per block
TOL = 3.0             # max mean |feature difference| (gray levels) for a block pair
MIN_STD = 8.0         # block texture threshold
MIN_BLOCKS = 6
VERIFY_NCC = 0.85
VERIFY_RES = 0.75    # local correlation of the fine-noise residuals (clean images: 99.9th pct 0.54)
AREA_MIN = 40         # px of verified cloned core (soft-brush spots have small exact cores)


def block_pairs(g, valid):
    h, w = g.shape
    c = B // 4; bl = cv2.blur(g, (c, c))          # 4 x 4 grid of c x c cell means per block
    ys = np.arange(0, h - B + 1, STEP); xs = np.arange(0, w - B + 1, STEP)
    feats = np.stack([bl[ys[:, None] + c // 2 + c * a, xs[None, :] + c // 2 + c * b] for a in range(4) for b in range(4)], -1)
    feats = feats.reshape(-1, 16)
    yy, xx = np.meshgrid(ys, xs, indexing="ij"); pos = np.stack([xx.ravel(), yy.ravel()], 1)
    # texture and validity per block
    mean = cv2.blur(g, (B, B)); sq = cv2.blur(g * g, (B, B))
    std = np.sqrt(np.maximum(sq - mean * mean, 0))
    cy, cx = pos[:, 1] + B // 2, pos[:, 0] + B // 2
    ok = (std[cy, cx] >= MIN_STD) & valid[cy, cx] & valid[pos[:, 1], pos[:, 0]] & valid[np.minimum(pos[:, 1] + B - 1, h - 1), np.minimum(pos[:, 0] + B - 1, w - 1)]
    feats, pos = feats[ok], pos[ok]
    if len(feats) < 2: return np.zeros((0, 2), int), np.zeros((0, 2), int)
    f = (feats - feats.mean(1, keepdims=True)).astype(np.float32)
    idx = cv2.flann_Index(f, dict(algorithm=1, trees=4))          # KD-tree, approximate nearest neighbours
    nn, dist = idx.knnSearch(f, K + 1, params=dict(checks=64))
    P, S = [], []
    for k in range(1, K + 1):
        j = nn[:, k]; ok_ = j >= 0
        d = np.abs(f[j] - f).mean(1)
        sh = pos[j] - pos
        far = np.hypot(sh[:, 0], sh[:, 1]) >= MIN_DIST
        sel = ok_ & (d <= TOL) & far
        a, s = pos[sel], sh[sel]
        flip = (s[:, 0] < 0) | ((s[:, 0] == 0) & (s[:, 1] < 0))      # canonical direction
        a = np.where(flip[:, None], a + s, a); s = np.where(flip[:, None], -s, s)
        P.append(a); S.append(s)
    return np.concatenate(P), np.concatenate(S)


def detect(rgb):
    rgb = fit(rgb); g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32); h, w = g.shape
    valid = mask_watermark(h, w) > 0
    P, S = block_pairs(g, valid)
    if len(S) == 0: return []
    # group shifts within +-1 px
    cnt = Counter(map(tuple, S)); out = []
    seen = set()
    for (dx, dy), n in cnt.most_common(20):
        if (dx, dy) in seen: continue
        near = [(dx + i, dy + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
        seen |= set(near)
        tot = sum(cnt.get(s, 0) for s in near)
        if tot < MIN_BLOCKS: break
        # verify with the exact (most common) shift
        M = np.float32([[1, 0, -dx], [0, 1, -dy]])        # warped(p) = g(p + shift)
        sh = cv2.warpAffine(g, M, (w, h), borderValue=-1)
        vm = valid & (sh >= 0) & (cv2.warpAffine(valid.astype(np.float32), M, (w, h)) > 0.5)
        ncc, std = _local_ncc(g, np.where(vm, sh, 0), win=9)
        # a copy also repeats the fine pixel noise; look-alike texture (fibres, gradients) does not
        rr = g - cv2.GaussianBlur(g, (0, 0), 1.0); rs = sh - cv2.GaussianBlur(sh, (0, 0), 1.0)
        nres, _ = _local_ncc(rr, np.where(vm, rs, 0), win=9)
        reg = (ncc > VERIFY_NCC) & (nres > VERIFY_RES) & (std > MIN_STD) & vm
        # only where the block pairs said so (avoids accepting unrelated look-alike areas)
        seed = np.zeros((h, w), np.uint8)
        sel = (np.abs(S[:, 0] - dx) <= 1) & (np.abs(S[:, 1] - dy) <= 1)
        seed[P[sel, 1], P[sel, 0]] = 1
        seed = cv2.dilate(seed, np.ones((B, B), np.uint8), anchor=(0, 0))
        reg &= seed > 0
        reg = cv2.morphologyEx(reg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)) > 0
        area = int(reg.sum())
        if area < AREA_MIN: continue
        src = reg; dst = cv2.warpAffine(reg.astype(np.uint8), np.float32([[1, 0, dx], [0, 1, dy]]), (w, h)) > 0
        out.append({"area": area, "blocks": int(tot), "shift": [int(dx), int(dy)], "source": src, "target": dst})
    out.sort(key=lambda d: -d["area"])
    return out


def overlay(rgb, found, path, zoom=True):
    rgb = fit(rgb); im = rgb.astype(np.float32).copy()
    cols = [(255, 140, 0), (0, 160, 255), (220, 0, 220)]
    for k, d in enumerate(found[:3]):
        c = cols[k % 3]
        for m in (d["source"], d["target"]):
            cnt, _ = cv2.findContours(cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(im, cnt, -1, c, 2)
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(path)


def _scan(path):
    try: rgb = np.asarray(Image.open(path).convert("RGB"))
    except Exception as e: return {"error": str(e)[:80]}
    f = detect(rgb)
    return {"area": f[0]["area"] if f else 0, "found": [{k: v for k, v in d.items() if k not in ("source", "target")} for d in f]}


def synth(src_dir, out_dir, n, seed=7):
    rng = random.Random(seed); files = sorted(Path(src_dir).glob("*.jpg")); rng.shuffle(files)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True); meta = []
    for f in files[:n]:
        rgb = fit(np.asarray(Image.open(f).convert("RGB"))).copy(); h, w = rgb.shape[:2]
        g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        s = rng.randint(14, 34); n_spots = rng.randint(1, 3)
        fake = rgb.astype(np.float32).copy(); spots = []
        for _ in range(n_spots):
            for _ in range(100):
                x0, y0 = rng.randint(0, w - s - 1), rng.randint(0, int(0.85 * h) - s - 1)
                dx, dy = rng.randint(-120, 120), rng.randint(-120, 120)
                x1, y1 = x0 + dx, y0 + dy
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
    ap.add_argument("--jobs", type=int, default=2); ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    if a.mode == "show":
        rgb = np.asarray(Image.open(a.a).convert("RGB")); f = detect(rgb); overlay(rgb, f, a.b)
        for d in f: print({k: v for k, v in d.items() if k not in ("source", "target")})
    elif a.mode == "synth": synth(a.a, a.b, a.n)
    elif a.mode == "validate":
        d = Path(a.a); meta = json.loads((d / "meta.json").read_text())
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [str(d / m["file"]) for m in meta]))
        for m, r in zip(meta, res): m.update(area=r.get("area", 0), found=r.get("found", []))
        pos = [m for m in meta if m["file"].startswith("pos")]; neg = [m for m in meta if m["file"].startswith("neg")]
        for thr in (AREA_MIN, 200, 400):
            print(f"area >= {thr}: detected {sum(m['area'] >= thr for m in pos)}/{len(pos)}, false alarms {sum(m['area'] >= thr for m in neg)}/{len(neg)}")
        print("missed spot sizes:", sorted(m["size"] for m in pos if m["area"] < AREA_MIN))
        print("false-alarm areas:", sorted([m["area"] for m in neg if m["area"] >= AREA_MIN], reverse=True)[:20])
        if a.out: a.out.write_text(json.dumps(meta, indent=1))
    else:
        recs = [json.loads(l) for l in Path(a.a).read_text().splitlines()]
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [str(Path(a.b) / r["file"]) for r in recs], chunksize=2))
        out = [{**r, **x} for r, x in zip(recs, res)]; a.out.write_text(json.dumps(out, indent=1))
        hits = sorted([o for o in out if o.get("area", 0) >= AREA_MIN], key=lambda o: -o["area"])
        print(f"{len(out)} images, {len(hits)} with a verified cloned spot")
        for o in hits[:30]: print(o["area"], o["found"][0]["shift"], o["catalog"], o["image_url"].split("/")[-1])


if __name__ == "__main__":
    main()

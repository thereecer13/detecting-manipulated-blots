"""Copy-move detection within single tissue (IHC) images.

1. Candidates: SIFT keypoints matched against the same image (2nd/3rd nearest neighbour ratio test,
   matches closer than MIN_DIST px ignored), then RANSAC for an affine map between the two point
   sets (covers plain copies and copies that were also slightly rotated or rescaled).
2. Verification: the image is warped by the found map and compared with itself pixel by pixel. A
   copy-move region is where the local normalized correlation (window WIN) is above VERIFY_NCC and the
   tissue is textured (no flat white or empty background). Natural tissue never repeats itself
   pixel for pixel, so a verified area of AREA_MIN px or more is strong evidence of a duplicated region.
The watermark strip (bottom right, repeated letters) is masked.

    python pilot/copy_move.py scan  index.jsonl images_dir --out hits.json [--jobs 4]
    python pilot/copy_move.py show  image.jpg out.png          (overlay of the detected regions)
    python pilot/copy_move.py synth images_dir out_dir --n 200  (validation set: synthetic copy-moves)
"""
import argparse, json, random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

MIN_DIST = 30          # px; matches closer than this are the same structure
RATIO = 0.6
WIN = 15
VERIFY_NCC = 0.95
AREA_MIN = 900         # px of verified duplicated tissue (about 30 x 30)
MIN_TEXTURE = 6.0      # local gray std below this counts as flat (background, white space)


def mask_watermark(h, w):
    m = np.ones((h, w), np.uint8)
    m[int(0.86 * h):, int(0.45 * w):] = 0
    return m


def _local_ncc(a, b, win=WIN):
    k = (win, win)
    ma, mb = cv2.blur(a, k), cv2.blur(b, k)
    va = cv2.blur(a * a, k) - ma * ma; vb = cv2.blur(b * b, k) - mb * mb
    cov = cv2.blur(a * b, k) - ma * mb
    den = np.sqrt(np.maximum(va, 0) * np.maximum(vb, 0))
    return np.where(den > 1e-3, cov / np.maximum(den, 1e-3), 0), np.sqrt(np.maximum(va, 0))


MAX_SIDE = 1600       # larger images (some are 5000 px) are shrunk first: memory and speed


def fit(rgb):
    h, w = rgb.shape[:2]; s = MAX_SIDE / max(h, w)
    return rgb if s >= 1 else cv2.resize(rgb, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)


def detect(rgb, max_models=3):
    rgb = fit(rgb)
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    h, w = g.shape
    wm = mask_watermark(h, w)
    sift = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.02)
    kp, des = sift.detectAndCompute(g, wm)
    if des is None or len(kp) < 10: return []
    pts = np.float32([k.pt for k in kp])
    bf = cv2.BFMatcher(cv2.NORM_L2)
    gf = g.astype(np.float32)
    out = []
    # plain copies: the image's keypoints against themselves
    src, dst = _pairs(bf.knnMatch(des, des, k=3), pts, pts, same=True)
    out += _models(src, dst, gf, wm, max_models, mirror=False)
    # mirrored copies: keypoints of the left-right flipped image, mapped back to original coordinates
    kpf, desf = sift.detectAndCompute(cv2.flip(g, 1), cv2.flip(wm, 1))
    if desf is not None and len(kpf) >= 10:
        ptsf = np.float32([(w - 1 - k.pt[0], k.pt[1]) for k in kpf])
        src, dst = _pairs(bf.knnMatch(des, desf, k=2), pts, ptsf, same=False)
        out += _models(src, dst, gf, wm, max_models, mirror=True)
    # drop the same pair found in the other direction (source and target swapped)
    keep = []
    for d in sorted(out, key=lambda d: -d["area"]):
        if any((d["target"] & k["source"]).sum() > 0.5 * d["area"] for k in keep): continue
        keep.append(d)
    out = keep
    out.sort(key=lambda d: -d["area"])
    return out


def _pairs(knn, pts, pts2, same):
    src, dst = [], []
    for ms in knn:
        ms = [m for m in ms if not (same and m.trainIdx == m.queryIdx)]
        if len(ms) < 2: continue
        m1, m2 = ms[0], ms[1]
        if m1.distance < RATIO * m2.distance:
            p, q = pts[m1.queryIdx], pts2[m1.trainIdx]
            if np.hypot(*(p - q)) >= MIN_DIST: src.append(p); dst.append(q)
    return np.float32(src).reshape(-1, 2), np.float32(dst).reshape(-1, 2)


def _models(src, dst, gf, wm, max_models, mirror):
    h, w = gf.shape; out = []; used = np.zeros(len(src), bool)
    for _ in range(max_models):
        idx = np.where(~used)[0]
        if len(idx) < 4: break
        if mirror: M, inl = cv2.estimateAffine2D(src[idx], dst[idx], method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=4000)
        else: M, inl = cv2.estimateAffinePartial2D(src[idx], dst[idx], method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=4000)
        if M is None or inl is None or inl.sum() < 4: break
        inl = inl.ravel().astype(bool); used[idx[inl]] = True
        det = float(np.linalg.det(M[:, :2]))
        if mirror and not (-1.3 < det < -0.7): continue      # a mirror copy flips orientation, at about the same scale
        Mi = cv2.invertAffineTransform(M)
        used |= np.hypot(*(cv2.transform(dst[None], Mi)[0] - src).T) < 3
        warped = cv2.warpAffine(gf, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=-1)
        valid = (warped >= 0) & (wm > 0) & (cv2.warpAffine(wm.astype(np.float32), M, (w, h)) > 0.5)
        ncc, std = _local_ncc(gf, np.where(valid, warped, 0))
        reg = (ncc > VERIFY_NCC) & (std > MIN_TEXTURE) & valid
        reg = cv2.morphologyEx(reg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(reg, 8)
        keep = [i for i in range(1, n) if st[i][4] >= AREA_MIN]
        area = int(sum(st[i][4] for i in keep))
        if area == 0: continue
        target = np.isin(lab, keep)
        source = cv2.warpAffine(target.astype(np.uint8), Mi, (w, h), flags=cv2.INTER_NEAREST) > 0
        out.append({"area": area, "inliers": int(inl.sum()), "mirror": mirror, "scale": float(np.sqrt(abs(det))),
                    "rotation": float(np.degrees(np.arctan2(M[1, 0], M[0, 0]))), "shift": [float(M[0, 2]), float(M[1, 2])],
                    "M": M.tolist(), "target": target, "source": source})
    return out


def overlay(rgb, found, path):
    im = rgb.copy().astype(np.float32)
    cols = [(255, 140, 0), (0, 160, 255), (220, 0, 220)]
    for k, d in enumerate(found[:3]):
        c = np.array(cols[k % 3], np.float32)
        for m in (d["source"], d["target"]):
            im[m] = 0.55 * im[m] + 0.45 * c
            cnt, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(im, cnt, -1, tuple(int(x) for x in c), 2)
    Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)).save(path)


def _scan(args):
    path, = args
    try: rgb = np.asarray(Image.open(path).convert("RGB"))
    except Exception as e: return {"error": str(e)[:80]}
    f = detect(rgb)
    return {"area": f[0]["area"] if f else 0, "found": [{k: v for k, v in d.items() if k not in ("target", "source")} for d in f]}


def synth(src_dir, out_dir, n, seed=5):
    """Copy a random textured patch to another place (half plain, half rotated/rescaled a little),
    re-save as JPEG q85; also save the untouched image re-saved the same way as a negative."""
    rng = random.Random(seed); files = sorted(Path(src_dir).glob("*.jpg")); rng.shuffle(files)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); meta = []
    for f in files[:n]:
        rgb = np.asarray(Image.open(f).convert("RGB")).copy(); h, w = rgb.shape[:2]
        s = rng.randint(40, 140)
        for _ in range(50):
            x0, y0 = rng.randint(0, w - s - 1), rng.randint(0, int(0.85 * h) - s - 1)
            x1, y1 = rng.randint(0, w - s - 1), rng.randint(0, int(0.85 * h) - s - 1)
            if abs(x0 - x1) > s or abs(y0 - y1) > s:
                if cv2.cvtColor(rgb[y0:y0 + s, x0:x0 + s], cv2.COLOR_RGB2GRAY).std() > 12: break
        patch = rgb[y0:y0 + s, x0:x0 + s].copy(); kind = "plain"
        r = rng.random()
        if r < 0.25:
            patch = patch[:, ::-1].copy(); kind = "mirror"
        elif r < 0.6:
            ang, sc = rng.uniform(-10, 10), rng.uniform(0.9, 1.1); kind = f"rot{ang:.0f}_sc{sc:.2f}"
            M = cv2.getRotationMatrix2D((s / 2, s / 2), ang, sc); patch = cv2.warpAffine(patch, M, (s, s), borderMode=cv2.BORDER_REFLECT)
        fake = rgb.copy(); fake[y1:y1 + s, x1:x1 + s] = patch
        Image.fromarray(fake).save(out_dir / f"pos_{f.stem}.jpg", quality=85)
        Image.fromarray(rgb).save(out_dir / f"neg_{f.stem}.jpg", quality=85)
        meta.append({"file": f"pos_{f.stem}.jpg", "size": s, "kind": kind}); meta.append({"file": f"neg_{f.stem}.jpg"})
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["scan", "show", "synth", "validate"])
    ap.add_argument("a"); ap.add_argument("b", nargs="?"); ap.add_argument("--out", type=Path)
    ap.add_argument("--jobs", type=int, default=2); ap.add_argument("--n", type=int, default=200)
    a = ap.parse_args()
    if a.mode == "show":
        rgb = fit(np.asarray(Image.open(a.a).convert("RGB"))); f = detect(rgb); overlay(rgb, f, a.b)
        for d in f: print({k: v for k, v in d.items() if k not in ("target", "source", "M")})
    elif a.mode == "synth":
        synth(a.a, a.b, a.n)
    elif a.mode == "validate":
        d = Path(a.a); meta = json.loads((d / "meta.json").read_text())
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [(str(d / m["file"]),) for m in meta]))
        for m, r in zip(meta, res): m.update(area=r.get("area", 0))
        pos = [m for m in meta if m["file"].startswith("pos")]; neg = [m for m in meta if m["file"].startswith("neg")]
        for thr in (900, 1500, 2500):
            print(f"area >= {thr}: detected {sum(m['area'] >= thr for m in pos)}/{len(pos)} "
                  f"(plain {sum(m['area'] >= thr for m in pos if m['kind'] == 'plain')}/{sum(m['kind'] == 'plain' for m in pos)}), "
                  f"false alarms {sum(m['area'] >= thr for m in neg)}/{len(neg)}")
        miss = [m for m in pos if m["area"] < 900]; print("missed sizes:", sorted(m["size"] for m in miss)[:30])
        if a.out: a.out.write_text(json.dumps(meta, indent=1))
    else:
        recs = [json.loads(l) for l in Path(a.a).read_text().splitlines()]
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_scan, [(str(Path(a.b) / r["file"]),) for r in recs], chunksize=2))
        out = [{**r, **x} for r, x in zip(recs, res)]
        a.out.write_text(json.dumps(out, indent=1))
        hits = sorted([o for o in out if o.get("area", 0) >= AREA_MIN], key=lambda o: -o["area"])
        print(f"{len(out)} images, {len(hits)} with a verified duplicated region")
        for o in hits[:30]: print(o["area"], o["catalog"], o["image_url"].split("/")[-1])


if __name__ == "__main__":
    main()

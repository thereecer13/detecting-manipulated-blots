"""Find colony-assay plates (wells/dishes) that are reused within a paper, also when rotated, mirrored
or rescaled.

1. Plates: circles found with a Hough transform in each figure (light round area with dark colonies).
2. Each plate is cropped to its bounding square, resized to S px and masked outside the rim.
3. Every pair of plates in a paper (same or different figures) is compared: SIFT keypoints (colonies
   are blobs) matched with the ratio test, then RANSAC for a similarity transform (rotation, scale,
   shift); the mirrored second plate is tried as well. A pair is a hit when enough colonies line up
   (INLIERS) and the aligned plates agree pixel for pixel inside the rim (VERIFY_NCC).

    python pilot/plate_dupes.py scan figs.json --out hits.json       (figs.json: [{pmcid, file, caption}])
    python pilot/plate_dupes.py validate figs.json                   (rotated/mirrored copies vs other plates)
    python pilot/plate_dupes.py show hits.json out_dir               (side-by-side images of each hit)
"""
import argparse, itertools, json, random
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

S = 192
INLIERS = 12
VERIFY_NCC = 0.8
RATIO = 0.75


def rim_score(gx, gy, x, y, r):
    """Share of points on the circle where the image gradient is strong and points across the rim."""
    t = np.linspace(0, 2 * np.pi, 96, endpoint=False)
    px = np.clip((x + r * np.cos(t)).astype(int), 0, gx.shape[1] - 1); py = np.clip((y + r * np.sin(t)).astype(int), 0, gx.shape[0] - 1)
    radial = np.abs(gx[py, px] * np.cos(t) + gy[py, px] * np.sin(t)); mag = np.hypot(gx[py, px], gy[py, px]) + 1e-6
    return float(((radial > 25) & (radial / mag > 0.7)).mean())


def circles(rgb):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); h, w = g.shape; L = max(h, w)
    c = cv2.HoughCircles(cv2.medianBlur(g, 5), cv2.HOUGH_GRADIENT, dp=1.0, minDist=0.03 * L, param1=120, param2=45,
                         minRadius=max(14, int(0.02 * L)), maxRadius=int(0.12 * L))
    if c is None: return []
    gb = cv2.GaussianBlur(g, (0, 0), 1.5).astype(np.float32)
    gx, gy = cv2.Sobel(gb, cv2.CV_32F, 1, 0), cv2.Sobel(gb, cv2.CV_32F, 0, 1)
    cand = []
    for x, y, r in c[0]:
        x, y, r = int(x), int(y), int(r)
        if x - r < 0 or y - r < 0 or x + r > w or y + r > h: continue
        rs = max(rim_score(gx, gy, x, y, r + d) for d in (-2, -1, 0, 1, 2))
        if rs < 0.55: continue                         # no continuous rim: not a dish or well
        crop = g[y - r:y + r, x - r:x + r]
        yy, xx = np.mgrid[:2 * r, :2 * r]; v = crop[np.hypot(yy - r, xx - r) < 0.85 * r]
        if v.std() < 8: continue                      # empty / flat circle (marker, symbol)
        if np.median(v) < 120: continue               # stained plates are light with dark colonies (not dark imaging)
        cand.append((rs, x, y, r))
    out = []
    for rs, x, y, r in sorted(cand, reverse=True):     # keep the best of overlapping circles
        if all(np.hypot(x - x2, y - y2) > 0.8 * max(r, r2) for x2, y2, r2 in out): out.append((x, y, r))
    return out


def plate_crop(rgb, x, y, r):
    g = cv2.cvtColor(rgb[y - r:y + r, x - r:x + r], cv2.COLOR_RGB2GRAY)
    g = cv2.resize(g, (S, S), interpolation=cv2.INTER_AREA if 2 * r > S else cv2.INTER_CUBIC)
    yy, xx = np.mgrid[:S, :S]; m = np.hypot(yy - S / 2, xx - S / 2) < 0.88 * S / 2
    return g, m


_sift = None
def feats(g, m):
    global _sift
    if _sift is None: _sift = cv2.SIFT_create(contrastThreshold=0.02)
    return _sift.detectAndCompute(g, m.astype(np.uint8))


def match(A, B):
    """A, B: (gray, mask, kp, des). Best (inliers, ncc, mirrored, M) over plain and mirrored B."""
    best = (0, -1.0, False, None)
    ga, ma, ka, da = A
    for mirror in (False, True):
        gb, mb = (cv2.flip(B[0], 1), cv2.flip(B[1], 1)) if mirror else (B[0], B[1])
        kb, db = feats(gb, mb) if mirror else (B[2], B[3])
        if da is None or db is None or len(ka) < 6 or len(kb) < 6: continue
        knn = cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2)
        good = [p[0] for p in knn if len(p) == 2 and p[0].distance < RATIO * p[1].distance]
        if len(good) < INLIERS: continue
        src = np.float32([ka[m.queryIdx].pt for m in good]); dst = np.float32([kb[m.trainIdx].pt for m in good])
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=3000)
        if M is None: continue
        n = int(inl.sum()); sc = float(np.sqrt(abs(np.linalg.det(M[:, :2]))))
        if n < INLIERS or not 0.8 < sc < 1.25: continue
        cx, cy = M @ np.array([S / 2, S / 2, 1.0])            # a reused plate maps centre onto centre
        if np.hypot(cx - S / 2, cy - S / 2) > 0.15 * S: continue
        wa = cv2.warpAffine(ga.astype(np.float32), M, (S, S)); wm = cv2.warpAffine(ma.astype(np.uint8), M, (S, S)) > 0
        v = wm & mb
        if v.sum() < 0.3 * mb.sum(): continue
        x, y = wa[v], gb.astype(np.float32)[v]
        ncc = float(np.corrcoef(x, y)[0, 1]) if x.std() > 1 and y.std() > 1 else -1
        if (n, ncc) > best[:2]: best = (n, ncc, mirror, M)
    return best


def load_plates(figs):
    plates = []
    for f in figs:
        try: rgb = np.asarray(Image.open(f["file"]).convert("RGB"))
        except Exception: continue
        for (x, y, r) in circles(rgb):
            g, m = plate_crop(rgb, x, y, r); kp, des = feats(g, m)
            plates.append({"pmcid": f["pmcid"], "file": f["file"], "xyr": (x, y, r), "g": g, "m": m, "kp": kp, "des": des})
    return plates


def same_figure(f1, f2):
    import re
    base = lambda f: re.sub(r"(_(OC|PB|HTML|lrg|web|print))?\.\w+$", "", Path(f).name, flags=re.I)
    return base(f1) == base(f2)


def _paper(figs):
    plates = load_plates(figs); hits = []
    for i, j in itertools.combinations(range(len(plates)), 2):
        a, b = plates[i], plates[j]
        if a["file"] == b["file"]:
            (x1, y1, r1), (x2, y2, r2) = a["xyr"], b["xyr"]
            if np.hypot(x1 - x2, y1 - y2) < r1 + r2: continue            # overlapping circles: the same pixels
        elif same_figure(a["file"], b["file"]): continue                   # colour / print renditions of one figure
        n, ncc, mir, M = match((a["g"], a["m"], a["kp"], a["des"]), (b["g"], b["m"], b["kp"], b["des"]))
        if n >= INLIERS and ncc >= VERIFY_NCC:
            rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
            hits.append({"pmcid": a["pmcid"], "a": {"file": a["file"], "xyr": a["xyr"]}, "b": {"file": b["file"], "xyr": b["xyr"]},
                         "inliers": n, "ncc": ncc, "mirrored": mir, "rotation": rot, "scale": float(np.sqrt(abs(np.linalg.det(M[:, :2]))))})
    return len(plates), hits


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["scan", "validate", "show"])
    ap.add_argument("figs"); ap.add_argument("b", nargs="?"); ap.add_argument("--out", type=Path); ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    if a.mode == "scan":
        figs = json.loads(Path(a.figs).read_text()); by = defaultdict(list)
        for f in figs: by[f["pmcid"]].append(f)
        with ProcessPoolExecutor(a.jobs) as ex: res = list(ex.map(_paper, by.values()))
        hits = [h for _, hs in res for h in hs]; n = sum(k for k, _ in res)
        a.out.write_text(json.dumps(hits, indent=1))
        print(f"{len(by)} papers, {len(figs)} figures, {n} plates, {len(hits)} matching plate pairs in {len({h['pmcid'] for h in hits})} papers")
        for h in sorted(hits, key=lambda h: -h["inliers"])[:30]:
            print(h["pmcid"], h["inliers"], round(h["ncc"], 2), "mirrored" if h["mirrored"] else "", round(h["rotation"]), Path(h["a"]["file"]).name, Path(h["b"]["file"]).name)
    elif a.mode == "validate":
        figs = json.loads(Path(a.figs).read_text()); rng = random.Random(3)
        plates = load_plates(figs); rng.shuffle(plates); plates = plates[:300]
        print(len(plates), "plates")
        pos = neg = tp = fp = 0
        for k, p in enumerate(plates):
            # positive: the same plate rotated (any angle), sometimes mirrored, rescaled, re-compressed
            ang, sc, mir = rng.uniform(0, 360), rng.uniform(0.85, 1.15), rng.random() < 0.3
            M = cv2.getRotationMatrix2D((S / 2, S / 2), ang, sc); g2 = cv2.warpAffine(p["g"], M, (S, S), borderValue=255)
            if mir: g2 = cv2.flip(g2, 1)
            ok, enc = cv2.imencode(".jpg", g2, [cv2.IMWRITE_JPEG_QUALITY, 80]); g2 = cv2.imdecode(enc, 0)
            kp2, d2 = feats(g2, p["m"])
            n, ncc, _, _ = match((p["g"], p["m"], p["kp"], p["des"]), (g2, p["m"], kp2, d2)); pos += 1; tp += n >= INLIERS and ncc >= VERIFY_NCC
            # negative: a plate from another paper
            q = plates[(k + 1 + rng.randrange(len(plates) - 1)) % len(plates)]
            if q["pmcid"] == p["pmcid"]: continue
            n, ncc, _, _ = match((p["g"], p["m"], p["kp"], p["des"]), (q["g"], q["m"], q["kp"], q["des"])); neg += 1; fp += n >= INLIERS and ncc >= VERIFY_NCC
        print(f"rotated/mirrored copies found: {tp}/{pos}; plates from other papers matched: {fp}/{neg}")
    else:
        hits = json.loads(Path(a.figs).read_text()); out = Path(a.b); out.mkdir(parents=True, exist_ok=True)
        for k, h in enumerate(hits):
            ims = []
            for s in ("a", "b"):
                rgb = np.asarray(Image.open(h[s]["file"]).convert("RGB")); x, y, r = h[s]["xyr"]
                ims.append(Image.fromarray(np.ascontiguousarray(rgb[y - r:y + r, x - r:x + r])).resize((300, 300)))
            c = Image.new("RGB", (610, 300), "white"); c.paste(ims[0], (0, 0)); c.paste(ims[1], (310, 0)); c.save(out / f"hit{k:03d}_{h['pmcid']}.png")


if __name__ == "__main__":
    main()

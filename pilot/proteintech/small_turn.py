"""Small copied patches that were also turned, resized or mirrored (not pixel-exact), in single IHC images.

copy_move.py fits one transform to all self-matches of an image, so a patch of a few hundred pixels is
lost among chance matches. Here every self-match is a seed: the matches around it (source and target both
within R px) are fitted locally (rotation + scale + shift; mirrored copies via the flipped image), and the
fitted map is then verified on the pixels as in copy_move.py but with looser limits.

    python3 small_turn.py OUT.json IMAGE [IMAGE ...]        hits per image: area, inliers, rotation, scale, mirror, boxes
"""
import sys, json
from pathlib import Path
import cv2, numpy as np
from PIL import Image
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).parent.parent))
import copy_move as cm

R, RATIO, MIN_INL, NCC, AREA = 45, 0.75, 5, 0.85, 150


def pairs(knn, pts, pts2, same):
    s, d = [], []
    for ms in knn:
        ms = [m for m in ms if not (same and m.trainIdx == m.queryIdx)]
        if len(ms) >= 2 and ms[0].distance < RATIO * ms[1].distance:
            p, q = pts[ms[0].queryIdx], pts2[ms[0].trainIdx]
            if np.hypot(*(p - q)) >= cm.MIN_DIST: s.append(p); d.append(q)
    return np.float32(s).reshape(-1, 2), np.float32(d).reshape(-1, 2)


def local_models(src, dst, mirror, w):
    """Local fits around each match. For mirrored copies dst is reflected first so a rotation+scale fits."""
    if len(src) < MIN_INL: return []
    d2 = dst.copy()
    if mirror: d2[:, 0] = w - 1 - d2[:, 0]
    ts, td = cKDTree(src), cKDTree(d2); out = []; seen = np.zeros(len(src), bool)
    for i in range(len(src)):
        if seen[i]: continue
        nb = sorted(set(ts.query_ball_point(src[i], R)) & set(td.query_ball_point(d2[i], R)))
        if len(nb) < MIN_INL: continue
        M, inl = cv2.estimateAffinePartial2D(src[nb], d2[nb], method=cv2.RANSAC, ransacReprojThreshold=2.0, maxIters=2000)
        if M is None or inl.sum() < MIN_INL: continue
        sc = float(np.hypot(M[0, 0], M[1, 0]))
        if not 0.7 < sc < 1.4: continue
        seen[np.array(nb)[inl.ravel() > 0]] = True
        if mirror: M = np.array([[-1, 0, w - 1], [0, 1, 0]], float) @ np.vstack([M, [0, 0, 1]])
        out.append((M.astype(np.float64), int(inl.sum()), sc))
    return out


def verify(gf, wm, M, cx, cy):
    """Pixel agreement under M, counted only in the neighbourhood of the fitted matches."""
    h, w = gf.shape; Mi = cv2.invertAffineTransform(M)
    warped = cv2.warpAffine(gf, Mi, (w, h), flags=cv2.INTER_LINEAR, borderValue=-1)      # target brought onto source
    valid = (warped >= 0) & (wm > 0) & (cv2.warpAffine(wm.astype(np.float32), Mi, (w, h)) > 0.5)
    ncc, std = cm._local_ncc(gf, np.where(valid, warped, 0))
    reg = ((ncc > NCC) & (std > cm.MIN_TEXTURE) & valid).astype(np.uint8)
    reg = cv2.morphologyEx(reg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(reg, 8); best = None
    for k in range(1, n):
        x, y, bw, bh, a = st[k]
        if a >= AREA and x - R <= cx <= x + bw + R and y - R <= cy <= y + bh + R and (best is None or a > best[4]): best = (x, y, bw, bh, a)
    if best is None: return None
    x, y, bw, bh, a = [int(v) for v in best]
    c = cv2.transform(np.float32([[[x, y], [x + bw, y], [x, y + bh], [x + bw, y + bh]]]), M)[0]
    return {"area": a, "src": [x, y, x + bw, y + bh], "dst": [int(c[:, 0].min()), int(c[:, 1].min()), int(c[:, 0].max()), int(c[:, 1].max())]}


def detect(rgb):
    rgb = cm.fit(rgb); g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY); h, w = g.shape; wm = cm.mask_watermark(h, w)
    sift = cv2.SIFT_create(nfeatures=0, contrastThreshold=0.015); bf = cv2.BFMatcher(cv2.NORM_L2); gf = g.astype(np.float32)
    kp, des = sift.detectAndCompute(g, wm)
    if des is None or len(kp) < 20: return []
    pts = np.float32([k.pt for k in kp]); cand = []
    s, d = pairs(bf.knnMatch(des, des, k=3), pts, pts, True)
    cand += [(M, n, sc, False, s, d) for M, n, sc in local_models(s, d, False, w)]
    kpf, desf = sift.detectAndCompute(cv2.flip(g, 1), cv2.flip(wm, 1))
    if desf is not None and len(kpf) >= 20:
        ptsf = np.float32([(w - 1 - k.pt[0], k.pt[1]) for k in kpf])
        s2, d2 = pairs(bf.knnMatch(des, desf, k=2), pts, ptsf, False)
        cand += [(M, n, sc, True, s2, d2) for M, n, sc in local_models(s2, d2, True, w)]
    hits = []
    for M, n, sc, mir, s, d in sorted(cand, key=lambda c: -c[1]):
        ok = np.hypot(*(cv2.transform(s[None], M)[0] - d).T) < 2.5; cx, cy = s[ok].mean(0) if ok.any() else (0, 0)
        v = verify(gf, wm, M, cx, cy)
        if v is None: continue
        rot = float(np.degrees(np.arctan2(M[1, 0], -M[0, 0] if mir else M[0, 0])))
        v.update(inliers=n, mirror=mir, scale=round(sc, 3), rotation=round(rot, 1), M=M.tolist())
        if any(abs(v["src"][0] - k["src"][0]) < 20 and abs(v["src"][1] - k["src"][1]) < 20 and k["mirror"] == mir for k in hits): continue
        if any(abs(v["src"][0] - k["dst"][0]) < 20 and abs(v["src"][1] - k["dst"][1]) < 20 and k["mirror"] == mir for k in hits): continue
        hits.append(v)
    return hits


if __name__ == "__main__":
    out = {}
    for p in sys.argv[2:]:
        try: out[Path(p).name] = detect(np.asarray(Image.open(p).convert("RGB")))
        except Exception as e: out[Path(p).name] = {"error": str(e)[:100]}
        print(Path(p).name, [(h["area"], h["inliers"], h["rotation"], h["scale"], "MIR" if h["mirror"] else "") for h in out[Path(p).name]] if isinstance(out[Path(p).name], list) else out[Path(p).name], flush=True)
    json.dump(out, open(sys.argv[1], "w"))

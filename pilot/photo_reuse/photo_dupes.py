"""Find photographic regions that appear twice in one paper's figures (same or different figure).

Works on any photo-like panel (cell-culture micrographs, mouse bioluminescence images): no panel
detector, just keypoints.

1. Photo mask: pixels whose neighbourhood is almost free of near-white pixels, so charts, text on
   white and gutters carry no keypoints. With dark=False, dark-background regions (fluorescence) are
   dropped too.
2. SIFT keypoints inside the mask.
3. Every figure is matched against itself and against every other figure of the paper, plain and
   mirrored. Matches are fitted with a similarity transform (RANSAC); a hit needs MIN_INL inliers
   spread over at least MIN_SPAN pixels in both directions (for mirrored
   matches the transform M maps the mirrored first figure onto the second), which removes repeated labels and scale
   bars. Self-matches that are the identity are ignored.
4. Each hit gets "ncc", the pixel correlation of the two regions after alignment. Triage keeps
   hits with ncc >= 0.5.

A hit says only that two regions show the same pixels. Whether that is a problem (different
samples) or fine (inset, same sample, merged channel) needs the labels and caption.
"""
import math
from pathlib import Path
import cv2
import numpy as np

MAXSIDE = 1600
MIN_INL = 22
MIN_SPAN = 45
RATIO = 0.72


def load(path):
    im = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if im is None: return None, 1.0
    h, w = im.shape[:2]; s = min(1.0, MAXSIDE / max(h, w))
    if s < 1: im = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    return im, s


def photo_mask(bgr, dark=True):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    white = (g > 232).astype(np.float32)
    frac = cv2.boxFilter(white, -1, (41, 41))
    m = (frac < 0.08).astype(np.uint8)
    if not dark:
        med = cv2.boxFilter(g.astype(np.float32), -1, (61, 61))
        m &= (med > 70).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_WIDTH] >= 70 and st[i, cv2.CC_STAT_HEIGHT] >= 70: keep[lab == i] = 1
    return g, keep


def feats(path, dark=True):
    bgr, s = load(path)
    if bgr is None: return None
    g, m = photo_mask(bgr, dark)
    area = int(m.sum())
    if area < 70 * 70: return {"n": 0, "area": area, "shape": g.shape, "scale": s}
    sift = cv2.SIFT_create(nfeatures=7000, contrastThreshold=0.03)
    out = {"area": area, "shape": g.shape, "scale": s, "g": g}
    for tag, gg, mm in (("p", g, m), ("f", g[:, ::-1].copy(), m[:, ::-1].copy())):
        kp, de = sift.detectAndCompute(gg, mm * 255)
        if de is None: kp, de = [], np.zeros((0, 128), np.float32)
        xy = np.array([k.pt for k in kp], np.float32).reshape(-1, 2)
        out[tag] = (xy, de)
    out["n"] = len(out["p"][0])
    return out


def _pairs(xa, da, xb, db, self_match, width=None):
    # width is given for a mirrored self-match: xa is in mirrored coordinates, and a symmetric blob
    # matching itself (same place once un-mirrored) is dropped.
    if width is not None:
        xa_plain = xa.copy(); xa_plain[:, 0] = width - 1 - xa_plain[:, 0]
    else: xa_plain = xa
    if len(da) < MIN_INL or len(db) < MIN_INL: return np.zeros((0, 2), np.float32), np.zeros((0, 2), np.float32)
    k = 3 if self_match else 2
    bf = cv2.BFMatcher(cv2.NORM_L2)
    src, dst = [], []
    for ms in bf.knnMatch(da, db, k=k):
        if self_match or width is not None: ms = [m for m in ms if np.hypot(*(xa_plain[m.queryIdx] - xb[m.trainIdx])) > 12]
        if len(ms) < 2: continue
        a, b = ms[0], ms[1]
        if a.distance < RATIO * b.distance and a.distance < 260:
            src.append(xa[a.queryIdx]); dst.append(xb[a.trainIdx])
    return np.array(src, np.float32).reshape(-1, 2), np.array(dst, np.float32).reshape(-1, 2)


def _fit(src, dst, self_match, mirrored, maxhits=4):
    hits = []
    for _ in range(maxhits):
        if len(src) < MIN_INL: break
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3.0, maxIters=3000, confidence=0.995)
        if M is None: break
        inl = inl.ravel().astype(bool); n = int(inl.sum())
        if n < MIN_INL: break
        s, d = src[inl], dst[inl]
        sc = math.hypot(M[0, 0], M[1, 0]); rot = math.degrees(math.atan2(M[1, 0], M[0, 0]))
        span = min(np.ptp(s[:, 0]), np.ptp(s[:, 1]), np.ptp(d[:, 0]), np.ptp(d[:, 1]))
        shift = float(np.median(np.hypot(*(d - s).T)))
        ok = span >= MIN_SPAN and 0.33 < sc < 3.0
        if self_match and not mirrored and shift < 25: ok = False            # the region matched to itself
        if ok:
            box = lambda p: [int(p[:, 0].min()), int(p[:, 1].min()), int(p[:, 0].max()), int(p[:, 1].max())]
            hits.append({"inliers": n, "scale": round(sc, 3), "rotation": round(rot, 1), "mirrored": mirrored,
                         "span": int(span), "abox": box(s), "bbox": box(d), "M": [[round(float(v), 4) for v in r] for r in M]})
        src, dst = src[~inl], dst[~inl]
    return hits


def _ncc(ga, gb, M, bbox, mirrored):
    """Pixel agreement inside the matched box after moving A onto B (1 = identical, about 0 = unrelated).
    Repeated textures (pads, cage bars, grids of similar panels) fit a transform but score low here."""
    if mirrored: ga = ga[:, ::-1]
    x0, y0, x1, y1 = bbox
    if x1 - x0 < 8 or y1 - y0 < 8: return 0.0
    w = cv2.warpAffine(ga, np.array(M, np.float32), (gb.shape[1], gb.shape[0]), flags=cv2.INTER_LINEAR, borderValue=255)
    a = w[y0:y1, x0:x1].astype(np.float32); b = gb[y0:y1, x0:x1].astype(np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.2); b = cv2.GaussianBlur(b, (0, 0), 1.2)
    a -= a.mean(); b -= b.mean(); d = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return round(float((a * b).sum() / d), 3) if d > 0 else 0.0


def _dedupe(hits):
    """A self-match is found in both directions; keep one of each mirror pair of boxes."""
    out = []
    for h in sorted(hits, key=lambda h: -h["inliers"]):
        dup = False
        for o in out:
            if o["a"] == h["b"] and o["b"] == h["a"] and _iou(o["abox"], h["bbox"]) > 0.4 and _iou(o["bbox"], h["abox"]) > 0.4: dup = True
            if o["a"] == h["a"] and o["b"] == h["b"] and _iou(o["abox"], h["abox"]) > 0.4 and _iou(o["bbox"], h["bbox"]) > 0.4: dup = True
        if not dup: out.append(h)
    return out


def _iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x1 - x0) * max(0, y1 - y0)
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0


def paper(files, dark=True):
    """files: list of figure paths. Returns (total photo area in pixels, hits)."""
    F = [(Path(f).name, feats(f, dark)) for f in files]
    F = [(n, f) for n, f in F if f and f["n"] >= MIN_INL]
    hits = []
    for i, (na, fa) in enumerate(F):
        for nb, fb in F[i:]:
            same = na == nb
            for mir in (False, True):
                xa, da = fa["f" if mir else "p"]; xb, db = fb["p"]
                W = fa["shape"][1]
                src, dst = _pairs(xa, da, xb, db, same and not mir, W if (same and mir) else None)
                for h in _fit(src, dst, same, mir):
                    h["ncc"] = _ncc(fa["g"], fb["g"], h["M"], h["bbox"], mir)
                    if mir: h["abox"] = [W - 1 - h["abox"][2], h["abox"][1], W - 1 - h["abox"][0], h["abox"][3]]
                    # coordinates back to the original figure's pixels
                    h["abox"] = [int(v / fa["scale"]) for v in h["abox"]]; h["bbox"] = [int(v / fb["scale"]) for v in h["bbox"]]
                    h["a"], h["b"] = na, nb; hits.append(h)
    return sum(f["area"] for _, f in F), _dedupe(hits)


if __name__ == "__main__":
    import sys, json
    print(json.dumps(paper(sys.argv[1:]), indent=1))

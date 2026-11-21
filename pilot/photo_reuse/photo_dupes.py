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
5. Each hit is grown to the whole area where the two images agree ("afull", "bfull"; see _extent).
   "abox"/"bbox" are only the bounding box of the matched keypoints and are usually too small.

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


def _extent(ga, gb, M, seed, mirrored, win=17, thr=0.55, step=6, gap=24):
    """Grow a hit to the whole rectangle in which the two images agree.

    The RANSAC inliers only cover where keypoints happened to be found, so their bounding box is
    usually smaller than the duplicated area. Here image A is moved onto image B with the fitted
    transform and the two are compared window by window (win x win pixels) on their fine detail
    (a band-pass, so that shared layout such as a scratch running down the middle of every panel
    does not count). A window is 'informative' when it is photographic in both images (few
    near-white pixels: this leaves out labels, axes and gutters) and textured in both; it 'agrees'
    when it also correlates >= thr.

    Starting from the inlier box, each side is pushed outwards one strip (step pixels) at a time
    for as long as at least 60% of the informative windows in the new strip (or, failing that, in
    the next four strips together) agree. Strips with
    almost nothing informative (flat background, a label box, a gutter) are crossed only if they
    are narrower than gap pixels and agreement resumes for 3 strips behind them, which is how a
    block of several duplicated panels is followed across its gutters.
    Returns (box in B, box in A, share of informative windows in the box that agree), boxes as
    [x0, y0, x1, y1] in the coordinates of ga / gb, or None when the inlier box itself fails.
    """
    Hb, Wb = gb.shape; Wa = ga.shape[1]
    src = ga[:, ::-1] if mirrored else ga
    M = np.array(M, np.float32)
    aw = cv2.warpAffine(src, M, (Wb, Hb), flags=cv2.INTER_LINEAR, borderValue=255)
    valid = cv2.warpAffine(np.full(src.shape, 255, np.uint8), M, (Wb, Hb), flags=cv2.INTER_NEAREST, borderValue=0) > 0
    k = (win, win)
    photo = (cv2.blur((aw > 232).astype(np.float32), k) < 0.3) & (cv2.blur((gb > 232).astype(np.float32), k) < 0.3) & valid
    band = lambda x: cv2.GaussianBlur(x, (0, 0), 1.0) - cv2.GaussianBlur(x, (0, 0), 4.0)
    a, b = band(aw.astype(np.float32)), band(gb.astype(np.float32))
    ma, mb = cv2.blur(a, k), cv2.blur(b, k)
    va, vb = cv2.blur(a * a, k) - ma * ma, cv2.blur(b * b, k) - mb * mb
    c = (cv2.blur(a * b, k) - ma * mb) / np.sqrt(np.maximum(va * vb, 1e-6))
    tex = (va > 2) & (vb > 2) & photo
    good = (c >= thr) & tex
    It, Ig = cv2.integral(tex.astype(np.uint8)), cv2.integral(good.astype(np.uint8))
    rect = lambda I, x0, y0, x1, y1: int(I[y1, x1] - I[y0, x1] - I[y1, x0] + I[y0, x0])

    def judge(x0, y0, x1, y1):
        """True: the strip agrees; False: it does not; None: too little in it to say."""
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(Wb, x1), min(Hb, y1)
        if x1 <= x0 or y1 <= y0: return False
        nt = rect(It, x0, y0, x1, y1)
        if nt < 0.12 * (x1 - x0) * (y1 - y0): return None
        return rect(Ig, x0, y0, x1, y1) >= 0.6 * nt

    x0, y0, x1, y1 = [int(v) for v in seed]
    if judge(x0, y0, x1, y1) is not True: return None

    def strip(side, d0, d1):          # the band from d0 to d1 pixels beyond one side of the current box
        return {"l": (x0 - d1, y0, x0 - d0, y1), "r": (x1 + d0, y0, x1 + d1, y1), "u": (x0, y0 - d1, x1, y0 - d0), "d": (x0, y1 + d0, x1, y1 + d1)}[side]

    moved = True
    while moved:
        moved = False
        for side in "lrud":
            while True:
                v = judge(*strip(side, 0, step)); adv = 0
                if v is True: adv = step
                elif v is False and judge(*strip(side, 0, 4 * step)) is True: adv = step     # one poor strip inside a good band
                elif v is None:                      # look across the uninformative band
                    for d in range(step, gap + 1, step):
                        w = judge(*strip(side, d, d + step))
                        if w is None: continue
                        if w is True and all(judge(*strip(side, d + i * step, d + (i + 1) * step)) is True for i in (1, 2)): adv = d + 3 * step
                        break
                if not adv: break
                if side == "l": x0 = max(0, x0 - adv)
                elif side == "r": x1 = min(Wb, x1 + adv)
                elif side == "u": y0 = max(0, y0 - adv)
                else: y1 = min(Hb, y1 + adv)
                moved = True
                if (side == "l" and x0 == 0) or (side == "r" and x1 == Wb) or (side == "u" and y0 == 0) or (side == "d" and y1 == Hb): break
    # windows are centred on their pixel and avoid white, so the box stops short of the photograph's
    # edge; take it out to the edge when that is within half a window
    inside = ((aw <= 232) & (gb <= 232) & valid).astype(np.uint8)
    for _ in range(win // 2 + 3):
        if x0 > 0 and inside[y0:y1, x0 - 1].mean() > 0.5: x0 -= 1
        if x1 < Wb and inside[y0:y1, x1].mean() > 0.5: x1 += 1
        if y0 > 0 and inside[y0 - 1, x0:x1].mean() > 0.5: y0 -= 1
        if y1 < Hb and inside[y1, x0:x1].mean() > 0.5: y1 += 1
    bfull = [x0, y0, x1, y1]
    Mi = cv2.invertAffineTransform(M)
    pts = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32) @ Mi[:, :2].T + Mi[:, 2]
    if mirrored: pts[:, 0] = Wa - 1 - pts[:, 0]
    afull = [int(max(0, pts[:, 0].min())), int(max(0, pts[:, 1].min())), int(min(Wa, pts[:, 0].max())), int(min(ga.shape[0], pts[:, 1].max()))]
    nt = rect(It, x0, y0, x1, y1)
    return bfull, afull, round(rect(Ig, x0, y0, x1, y1) / nt, 2) if nt else 0.0


def full_extent(path_a, path_b, h):
    """Full duplicated area for a stored hit (see _extent), in the pixels of the original figures."""
    A, sa = load(path_a); B, sb = load(path_b)
    ga, gb = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
    seed = [int(v * sb) for v in h["bbox"]]
    r = _extent(ga, gb, h["M"], seed, h["mirrored"])
    if r is None: return h["abox"], h["bbox"], None
    bfull, afull, share = r
    return [int(v / sa) for v in afull], [int(v / sb) for v in bfull], share


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
                    ext = _extent(fa["g"], fb["g"], h["M"], h["bbox"], mir)
                    if ext:      # the whole agreeing area, not just where keypoints fell
                        h["bfull"] = [int(v / fb["scale"]) for v in ext[0]]; h["afull"] = [int(v / fa["scale"]) for v in ext[1]]; h["agree"] = ext[2]
                    if mir: h["abox"] = [W - 1 - h["abox"][2], h["abox"][1], W - 1 - h["abox"][0], h["abox"][3]]
                    # coordinates back to the original figure's pixels
                    h["abox"] = [int(v / fa["scale"]) for v in h["abox"]]; h["bbox"] = [int(v / fb["scale"]) for v in h["bbox"]]
                    h["a"], h["b"] = na, nb; hits.append(h)
    return sum(f["area"] for _, f in F), _dedupe(hits)


if __name__ == "__main__":
    import sys, json
    print(json.dumps(paper(sys.argv[1:]), indent=1))

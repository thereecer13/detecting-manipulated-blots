"""Panel-to-panel duplication score for flow cytometry plots.

Two panels are compared on their "ink" (dots, contours) after axis and gate
lines are removed. For a set of scales the best translation is found by FFT
cross-correlation; the score counts textured blocks that agree at that
alignment. Sparse dot patterns are effectively random, so many agreeing
textured blocks means the same events are drawn in both panels.
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

FILL = (0.03, 0.40)
SCALES = [1.0, 0.6, 0.7, 0.8, 0.9, 1.1, 1.25, 1.43, 1.67]


def ink(im, maxside=None):
    """Greyscale ink map (0 = paper) with long straight lines removed."""
    if maxside and max(im.size) > maxside:
        im = im.copy()
        im.thumbnail((maxside, maxside), Image.LANCZOS)
    rgb = np.asarray(im.convert('RGB'), dtype=np.float32)
    # darkness or colour saturation both count as ink
    g = 255 - rgb.min(axis=2)
    bg = np.median(g)
    g = np.clip(g - bg, 0, None)
    L = max(15, min(g.shape) // 6)
    h = ndi.grey_opening(g, size=(1, L))
    v = ndi.grey_opening(g, size=(L, 1))
    lines = np.maximum(h, v)
    # a solid dense cloud also survives opening in both directions: keep it
    solid = np.minimum(h, v)
    g = g - np.clip(lines - solid, 0, None)
    return g


def _blocks(a, b, bs=12, st=6):
    """Blockwise NCC of two same-shape arrays; returns (ncc, textured mask)."""
    H, W = a.shape
    if H < bs or W < bs:
        return np.zeros((0, 0)), np.zeros((0, 0), bool)
    k = np.ones((bs, bs), np.float32) / (bs * bs)
    def box(x):
        return ndi.uniform_filter(x, bs, mode='constant')[bs // 2:H - bs // 2 + 1:st, bs // 2:W - bs // 2 + 1:st]
    ma, mb = box(a), box(b)
    va = box(a * a) - ma * ma
    vb = box(b * b) - mb * mb
    cov = box(a * b) - ma * mb
    ncc = cov / np.sqrt(np.clip(va, 1e-6, None) * np.clip(vb, 1e-6, None))
    # textured: real variation in both, and not saturated solid
    # sparse-dot blocks only: some ink, but not a solid cloud or a text glyph
    fa, fb = box((a > 40).astype(np.float32)), box((b > 40).astype(np.float32))
    tex = (va > 150) & (vb > 150) & (fa > FILL[0]) & (fa < FILL[1]) & (fb > FILL[0]) & (fb < FILL[1])
    return ncc, tex


def match(A, B, scales=SCALES, thr=0.7):
    """A, B: ink maps. Returns dict with score and best alignment."""
    best = {'score': 0.0, 'n': 0, 'frac': 0.0, 'scale': 1.0, 'dx': 0, 'dy': 0, 'ncc': 0.0}
    a0 = A - A.mean()
    for s in scales:
        if s == 1.0:
            Bs = B
        else:
            h, w = int(round(B.shape[0] * s)), int(round(B.shape[1] * s))
            if min(h, w) < 24:
                continue
            Bs = np.asarray(Image.fromarray(B).resize((w, h), Image.BILINEAR))
        b0 = Bs - Bs.mean()
        cc = fftconvolve(a0, b0[::-1, ::-1], mode='full')
        # require at least 30% of the smaller panel to overlap
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
        dy, dx = iy - (Bs.shape[0] - 1), ix - (Bs.shape[1] - 1)
        y0, x0 = max(0, dy), max(0, dx)
        y1, x1 = min(A.shape[0], dy + Bs.shape[0]), min(A.shape[1], dx + Bs.shape[1])
        if y1 - y0 < 24 or x1 - x0 < 24:
            continue
        pa = A[y0:y1, x0:x1]
        pb = Bs[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
        ncc, tex = _blocks(pa, pb)
        if not tex.size:
            continue
        nt = int(tex.sum())
        good = tex & (ncc > thr)
        n = int(good.sum())
        frac = n / max(nt, 1)
        # either map textured: penalise content present in one panel only
        score = n * frac
        if score > best['score']:
            best = {'score': float(score), 'n': n, 'frac': float(frac), 'scale': s,
                    'dx': int(dx), 'dy': int(dy),
                    'ncc': float(ncc[tex].mean()) if nt else 0.0,
                    'box': [int(x0), int(y0), int(x1), int(y1)]}
    return best


# ---- dot-level matching -------------------------------------------------
def dots(im, thr=50, max_area=14, max_box=5, border=0.05):
    """Centroids of small isolated ink specks (single events).

    Text, axis lines, gate lines and dense clouds form larger connected
    components and are dropped, as are tick marks near the panel border.
    Returns (points array of (y, x), image shape)."""
    rgb = np.asarray(im.convert('RGB'), dtype=np.float32)
    g = 255 - rgb.min(axis=2)
    g = np.clip(g - np.median(g), 0, None)
    lab, n = ndi.label(g > thr, structure=np.ones((3, 3)))
    H, W = g.shape
    if n == 0:
        return np.zeros((0, 2)), (H, W)
    sl = ndi.find_objects(lab)
    area = ndi.sum(np.ones_like(lab), lab, index=np.arange(1, n + 1))
    pts = []
    by, bx = border * H, border * W
    for i, s in enumerate(sl):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        if area[i] > max_area or h > max_box or w > max_box:
            continue
        cy, cx = (s[0].start + s[0].stop - 1) / 2, (s[1].start + s[1].stop - 1) / 2
        if cy < by or cy > H - by or cx < bx or cx > W - bx:
            continue
        pts.append((cy, cx))
    return np.array(pts).reshape(-1, 2), (H, W)


def _raster(pts, shape, r=0):
    m = np.zeros(shape, np.float32)
    if len(pts):
        y = np.clip(np.round(pts[:, 0]).astype(int), 0, shape[0] - 1)
        x = np.clip(np.round(pts[:, 1]).astype(int), 0, shape[1] - 1)
        m[y, x] = 1
    if r:
        m = ndi.maximum_filter(m, 2 * r + 1)
    return m


def match_dots(PA, PB, scales=SCALES, min_pts=8):
    """PA, PB from dots(). Best translation/scale by coincident-dot count.

    M = dots of B landing within 1 px of a dot of A at the best shift;
    S = the best count at any clearly different shift (chance level)."""
    (pa, sa), (pb, sb) = PA, PB
    best = {'score': 0.0, 'M': 0, 'S': 0, 'na': len(pa), 'nb': len(pb), 'scale': 1.0, 'dx': 0, 'dy': 0}
    if len(pa) < min_pts or len(pb) < min_pts:
        return best
    Am = _raster(pa, sa, r=1)
    for s in scales:
        shp = (int(round(sb[0] * s)) + 1, int(round(sb[1] * s)) + 1)
        Bm = _raster(pb * s, shp)
        cc = fftconvolve(Am, Bm[::-1, ::-1], mode='full')
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
        M = float(cc[iy, ix])
        c2 = cc.copy()
        c2[max(0, iy - 4):iy + 5, max(0, ix - 4):ix + 5] = 0
        S = float(c2.max())
        frac = M / min(len(pa), len(pb))
        score = (M - S) * min(1.0, frac * 2)
        if score > best['score']:
            best = {'score': score, 'M': int(round(M)), 'S': int(round(S)), 'frac': frac,
                    'na': len(pa), 'nb': len(pb), 'scale': s,
                    'dy': int(iy - (shp[0] - 1)), 'dx': int(ix - (shp[1] - 1))}
    return best

"""Decide whether a region of a figure lies inside a flow cytometry dot plot.

A flow plot is taken to be a framed panel (axis lines to the left of and
below the dots) that shows at least one of:
  - logarithmic tick marks on an axis (gaps shrink within each decade, then
    jump back), or
  - a gate drawn inside the frame: quadrant lines, a rectangle or a polygon
    around a population.
UMAP/t-SNE maps, icons, bar hatching and network diagrams have no such frame.
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def ink_of(im):
    rgb = np.asarray(im.convert('RGB'), dtype=np.float32)
    g = 255 - rgb.min(axis=2)
    return np.clip(g - np.median(g), 0, None)


def _runs(mask1d):
    """(start, stop) of True runs in a 1-D boolean array."""
    d = np.diff(np.concatenate([[0], mask1d.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0]))


def _ticks(profile, min_h=1):
    """Tick centres from a 1-D profile of dark-pixel counts across an axis."""
    return np.array([(a + b - 1) / 2 for a, b in _runs(profile >= min_h) if b - a <= 4])


def log_score(pos):
    """Number of 'decade' runs: >=3 consecutive gaps each 45-90% of the one before."""
    if len(pos) < 6:
        return 0
    g = np.diff(pos)
    g = g[g > 0]
    n, run = 0, 0
    for i in range(1, len(g)):
        r = g[i] / g[i - 1]
        if 0.45 <= r <= 0.92:
            run += 1
        else:
            if run >= 2:
                n += 1
            run = 0
    if run >= 2:
        n += 1
    return n


def panel(B, box, thr=60):
    """B: ink map of the figure. box: [x0, y0, x1, y1] of the matched dots.
    Returns a dict describing the enclosing plot, or {'frame': False}."""
    H, W = B.shape
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    dark = B > thr
    L = int(max(30, 0.6 * min(bw, bh)))
    # search window around the box
    mx, my = int(1.2 * bw) + 20, int(1.2 * bh) + 20
    wx0, wy0, wx1, wy1 = max(0, x0 - mx), max(0, y0 - my), min(W, x1 + mx), min(H, y1 + my)
    D = dark[wy0:wy1, wx0:wx1]
    hl = ndi.binary_opening(D, np.ones((1, L), bool))
    vl = ndi.binary_opening(D, np.ones((L, 1), bool))
    bx0, by0, bx1, by1 = x0 - wx0, y0 - wy0, x1 - wx0, y1 - wy0
    cyc, cxc = (by0 + by1) // 2, (bx0 + bx1) // 2
    # left axis: nearest vertical line at or left of the box covering most of its height
    def vcover(x):
        return vl[by0:by1 + 1, x].mean() if 0 <= x < D.shape[1] else 0
    def hcover(y):
        return hl[y, bx0:bx1 + 1].mean() if 0 <= y < D.shape[0] else 0
    xl = next((x for x in range(bx0 + 3, -1, -1) if vcover(x) > 0.7), None)
    yb = next((y for y in range(by1 - 3, D.shape[0]) if hcover(y) > 0.7), None)
    if xl is None or yb is None:
        return {'frame': False}
    xr = next((x for x in range(bx1 - 3, D.shape[1]) if vcover(x) > 0.7), None)
    yt = next((y for y in range(by0 + 3, -1, -1) if hcover(y) > 0.7), None)
    # extent of the axes
    col = vl[:, xl]
    top = min((a for a, b in _runs(col) if a <= cyc + bh and b >= by0), default=by0)
    row = hl[yb]
    right = max((b for a, b in _runs(row) if a <= bx1 and b >= bx0), default=bx1)
    px0, py0, px1, py1 = xl, (yt if yt is not None else top), (xr if xr is not None else right), yb
    pw, ph = px1 - px0, py1 - py0
    if pw < 40 or ph < 40:
        return {'frame': False}
    out = {'frame': True, 'closed': xr is not None and yt is not None,
           'panel': [int(px0 + wx0), int(py0 + wy0), int(px1 + wx0), int(py1 + wy0)]}
    # ticks: dark columns in thin bands just outside and just inside each axis
    best = 0
    for band in (D[py1 + 2:py1 + 6, px0:px1 + 1], D[py1 - 6:py1 - 1, px0 + 2:px1 - 1]):
        if band.size:
            best = max(best, log_score(_ticks(band.sum(0), 2)))
    for band in (D[py0:py1 + 1, max(0, px0 - 6):max(0, px0 - 1)], D[py0 + 2:py1 - 1, px0 + 2:px0 + 6]):
        if band.size:
            best = max(best, log_score(_ticks(band.sum(1), 2)))
    out['log_runs'] = int(best)
    # gates: long straight lines strictly inside the frame, or thin outlines (polygons)
    m = 5
    inner_h = hl[py0 + m:py1 - m, px0 + m:px1 - m]
    inner_v = vl[py0 + m:py1 - m, px0 + m:px1 - m]
    gate_h = bool(inner_h.size and (inner_h.sum(1) > 0.3 * pw).any())
    gate_v = bool(inner_v.size and (inner_v.sum(0) > 0.3 * ph).any())
    poly = False
    inner = D[py0 + m:py1 - m, px0 + m:px1 - m]
    if inner.size:
        lab, n = ndi.label(inner, structure=np.ones((3, 3)))
        for i, s in enumerate(ndi.find_objects(lab)):
            h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
            if h > 0.2 * ph and w > 0.2 * pw:
                fill = (lab[s] == i + 1).mean()
                if fill < 0.12:
                    poly = True
                    break
    out.update(gate_lines=gate_h or gate_v, quadrant=gate_h and gate_v, gate_outline=poly)
    out['facs'] = bool(out['log_runs'] >= 2 or out['gate_lines'] or poly)
    return out


def classify(im, boxes):
    B = ink_of(im)
    return [panel(B, b) for b in boxes]

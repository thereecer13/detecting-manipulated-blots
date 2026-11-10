import sys
import numpy as np, cv2
sys.path.insert(0, '/home/user/detecting-manipulated-blots/pilot')
from views import blot_mask
def background(g):
    m = blot_mask(g) & ~(cv2.dilate((g >= 240).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    if m.sum() < 500: return None
    band = cv2.dilate((g < np.percentile(g[m], 15)).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
    bg = cv2.erode((m & ~band).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    return bg if bg.sum() >= 300 else None
def metrics(g):
    """g: uint8 grayscale at native resolution (no resizing)."""
    bg = background(g)
    if bg is None: return None
    f = g.astype(np.float32)
    r1 = f - cv2.GaussianBlur(f, (0, 0), 1.0)
    amp = float(np.percentile(np.abs(r1[bg]), 95))
    levels = int(len(np.unique(g[bg])))
    # grid alignment: horizontal and vertical steps on each of the 8 column/row phases
    dx = np.abs(np.diff(f, axis=1)); mx = bg[:, 1:] & bg[:, :-1]
    dy = np.abs(np.diff(f, axis=0)); my = bg[1:] & bg[:-1]
    px = np.array([dx[:, p::8][mx[:, p::8]].mean() if mx[:, p::8].any() else 0 for p in range(8)])
    py = np.array([dy[p::8][my[p::8]].mean() if my[p::8].any() else 0 for p in range(8)])
    grid = float(((px.max() / max(px.mean(), 1e-6)) + (py.max() / max(py.mean(), 1e-6))) / 2)
    # spatial scale: autocorrelation of mid-scale texture (trend removed) at lags 1, 3, 6 px
    r3 = f - cv2.GaussianBlur(f, (0, 0), 6.0)
    x = np.where(bg, r3 - r3[bg].mean(), 0)
    def ac(l):
        a, b = x[:, :-l], x[:, l:]; m2 = bg[:, :-l] & bg[:, l:]
        return float((a[m2] * b[m2]).mean() / max((x[bg] ** 2).mean(), 1e-9))
    # share of background that is exactly flat (3x3 neighbourhood has one value)
    mn = cv2.erode(g, np.ones((3, 3), np.uint8)); mxv = cv2.dilate(g, np.ones((3, 3), np.uint8))
    flat = float(((mxv - mn) == 0)[bg].mean())
    return {"amp": amp, "levels": levels, "grid": grid, "ac1": ac(1), "ac3": ac(3), "ac6": ac(6), "flat": flat, "width": g.shape[1]}

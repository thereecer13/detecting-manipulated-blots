"""Forensic views that cannot clip to black: histogram-equalized, local contrast (CLAHE) and noise residual."""
import cv2
import numpy as np
from PIL import Image

def to_gray(img):
    return np.asarray(img.convert("L"))

def local_contrast(g, clip=3.0, tile=8):
    tiles = (max(2, g.shape[1] // 64), max(2, g.shape[0] // 64)) if tile is None else (tile, tile)
    return cv2.createCLAHE(clipLimit=clip, tileGridSize=tiles).apply(g)

def residual(g, sigma=1.5):
    f = g.astype(np.float32)
    r = f - cv2.GaussianBlur(f, (0, 0), sigma)
    mad = np.median(np.abs(r - np.median(r))) * 1.4826
    scale = max(mad, 0.5) * 4          # +-4 robust SDs span the gray range
    return np.clip(128 + r / scale * 127, 0, 255).astype(np.uint8)

def resize(a, s, nearest):
    h, w = a.shape
    return cv2.resize(a, (max(1, round(w * s)), max(1, round(h * s))),
                      interpolation=cv2.INTER_NEAREST if nearest else cv2.INTER_AREA if s < 1 else cv2.INTER_LANCZOS4)

def equalized(g):
    """Global histogram equalization: the most common gray levels (usually the background) get most of the
    output range, like raising the black point and lowering the white point by hand, but without clipping."""
    return cv2.equalizeHist(g)

def views(img, long_side=512):
    """Return {name: image} at long_side; forensic views are computed at native resolution."""
    g = to_gray(img); s = long_side / max(g.shape)
    up = s > 1   # upscale views with nearest-neighbour so pixel noise is not smoothed into fake texture
    return {"": Image.fromarray(resize(g, s, False)),
            "_equalized": Image.fromarray(resize(equalized(g), s, up)),
            "_local": Image.fromarray(resize(local_contrast(g), s, up)),
            "_residual": Image.fromarray(resize(residual(g), s, up))}

def clipped_fraction(view, original):
    """Share of pixels pushed to 0/255 by the view that were not already saturated in the original."""
    v = np.asarray(view); o = np.asarray(original)
    if o.shape != v.shape:
        o = cv2.resize(o, (v.shape[1], v.shape[0]), interpolation=cv2.INTER_NEAREST)
    new = ((v <= 2) | (v >= 253)) & ~((o <= 2) | (o >= 253))
    return float(new.mean())

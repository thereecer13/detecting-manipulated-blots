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

def blot_mask(g):
    """Pixels belonging to blot panels, not to the figure page around them.

    Page = near-white pixels connected to the image border. Everything else that forms a large
    region (>= 1.5% of the image) is a blot panel; small regions are text, ladder ticks and arrows.
    Each panel is taken as its bounding rectangle (membranes are rectangular), minus any page pixels
    inside that rectangle (white margin or ladder labels next to a strip). If no panel is found (the
    whole image is one blot crop, or the background is pure white), the whole image counts as blot."""
    h, w = g.shape
    white = (cv2.GaussianBlur(g, (3, 3), 0) >= 246).astype(np.uint8)
    n, lab = cv2.connectedComponents(white, 4)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    page = np.isin(lab, list(border)) & (white > 0)
    if page.mean() < 0.05:
        return np.ones_like(g, bool)
    rest = cv2.morphologyEx((~page).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(rest, 8)
    mask = np.zeros_like(g, bool)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area >= 0.015 * h * w and bw >= 0.05 * w and bh >= 0.05 * h:
            mask[y:y + bh, x:x + bw] = True
    mask &= ~page
    return mask if mask.any() else np.ones_like(g, bool)


def equalized(g):
    """Histogram equalization inside the blot panels only, using the panels' own gray levels: the
    most common levels there (usually the membrane background) get most of the output range, like
    raising the black point and lowering the white point by hand, without clipping. The page, labels
    and ladder text outside the panels are left as they are (equalizing them with the blot would let
    the white page take the bright end of the range and push the blot background to near black)."""
    m = blot_mask(g)
    vals = g[m]
    hist = np.bincount(vals, minlength=256).astype(np.float64)
    cdf = hist.cumsum(); cdf_min = cdf[cdf > 0][0]
    lut = np.clip(np.round((cdf - cdf_min) / max(cdf[-1] - cdf_min, 1) * 255), 0, 255).astype(np.uint8)
    out = g.copy(); out[m] = lut[g[m]]
    return out



def blot_mask_v2(g):
    """Like blot_mask, but the page may be light grey instead of white: the page level is taken from
    the image border (its most common grey level, if brighter than 200), and the page is every pixel
    within 6 grey levels of it that is connected to the border. Ladder ticks and labels that touch
    a panel are trimmed off its rectangle."""
    h, w = g.shape
    border = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])
    lvl = int(np.argmax(np.bincount(border, minlength=256)))
    if lvl < 200:
        return blot_mask(g)
    gb = cv2.GaussianBlur(g, (3, 3), 0).astype(np.int16)
    near = ((np.abs(gb - lvl) <= 6) | (gb >= 246)).astype(np.uint8)
    n, lab = cv2.connectedComponents(near, 4)
    ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    page = np.isin(lab, list(ids)) & (near > 0)
    if page.mean() < 0.05:
        return np.ones_like(g, bool)
    rest = cv2.morphologyEx((~page).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(rest, 8)
    mask = np.zeros_like(g, bool)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area >= 0.015 * h * w and bw >= 0.05 * w and bh >= 0.05 * h:
            comp = lab[y:y + bh, x:x + bw] == i
            # trim ladder ticks and labels that touch the panel: keep the columns and rows the panel fills
            cols = np.where(comp.mean(0) > 0.5)[0]; rows = np.where(comp.mean(1) > 0.5)[0]
            if len(cols) and len(rows):
                mask[y + rows.min():y + rows.max() + 1, x + cols.min():x + cols.max() + 1] = True
    mask &= ~page
    return mask if mask.any() else np.ones_like(g, bool)


def levels_richardson(g, width=30):
    """Richardson's Levels adjustment, applied inside the blot panels only.

    Fitted on 339 of his original / "_levels" image pairs (June 2026 release): a linear stretch of a
    30-grey-level window (gain 8.5, gamma 1) centred on the membrane background, residual 0.3 grey
    levels. Here the window is centred on the most common grey level of each blot panel, and pixels
    outside the panels (page, ladder labels, arrows) are left unchanged."""
    m = blot_mask_v2(g)
    out = g.copy()
    border = np.concatenate([g[0], g[-1], g[:, 0], g[:, -1]])
    page_lvl = int(np.argmax(np.bincount(border, minlength=256)))
    k = np.ones((11, 11), np.uint8)
    textured = cv2.dilate(g, k) != cv2.erode(g, k)      # not an exactly constant area (label box, fill)
    n, lab = cv2.connectedComponents(m.astype(np.uint8), 8)
    for i in range(1, n):
        pm = lab == i
        vals = g[pm]
        if vals.size < 200:
            continue
        counts = np.bincount(vals, minlength=256)
        top = int(np.argmax(counts))
        if counts[top] > 0.97 * vals.size and not (vals < top - 40).any():
            continue          # solid one-colour rectangle with no band: a chart bar, not a membrane
        tv = g[pm & textured]            # centre the window on the textured membrane when there is enough of it
        src = tv if tv.size > 0.2 * vals.size else vals
        if page_lvl >= 200:              # label areas at the page level inside a framed figure are not membrane
            off = src[np.abs(src.astype(np.int16) - page_lvl) > 8]
            if off.size > 0.15 * vals.size:
                src = off
        hist = np.convolve(np.bincount(src, minlength=256).astype(np.float64), np.ones(5) / 5, mode="same")
        bg = int(np.argmax(hist))
        below = vals[vals < bg - width / 2]
        if below.size > 0.3 * vals.size:   # most of the panel would clip to black: the membrane is the darker population
            hb = np.convolve(np.bincount(below, minlength=256).astype(np.float64), np.ones(5) / 5, mode="same")
            bg = int(np.argmax(hb))
        lo = bg - width / 2
        out[pm] = np.clip((vals.astype(np.float32) - lo) * (255.0 / width), 0, 255).astype(np.uint8)
    return out

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

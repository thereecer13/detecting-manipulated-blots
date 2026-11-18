"""Context checks for a matched pair of flow plots: is it the same plot cropped differently, a whole plot
shown again (and do its labels match), or only part of the dots shared?

  kind      'crop'    the two panels are one plot seen through different windows (inset, zoom, re-crop)
            'whole'   the whole plot repeats at the same position inside its frame
            'part'    only part of the content coincides
  same_title, same_text   for 'whole': the title strip above the plots / the text printed inside them match
"""
import numpy as np
from scipy import ndimage as ndi


def ink(im, box, pad=0):
    x0, y0, x1, y1 = box
    a = np.asarray(im.crop((x0 - pad, y0 - pad, x1 + 1 + pad, y1 + 1 + pad)).convert('RGB'), dtype=np.float32)
    return (255 - a.min(axis=2)) > 70


def _resize(m, s):
    if s == 1.0:
        return m
    return ndi.zoom(m.astype(np.float32), s, order=1) > 0.4


def _agree(a, b):
    """Share of ink pixels of either mask that have ink within 1 px in the other."""
    n = a.sum() + b.sum()
    if n < 30:
        return None
    da, db = ndi.binary_dilation(a, iterations=1), ndi.binary_dilation(b, iterations=1)
    return float(((a & db).sum() + (b & da).sum()) / n)


def _text(m):
    """Glyph-like components: bigger than a dot, smaller than a cloud, not a line."""
    lab, n = ndi.label(m, structure=np.ones((3, 3)))
    out = np.zeros_like(m)
    for i, s in enumerate(ndi.find_objects(lab)):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        if 5 <= h <= 26 and 2 <= w <= 26 and (lab[s] == i + 1).sum() >= 8:
            out[s] |= lab[s] == i + 1
    # keep glyphs that sit in a row of glyphs (a word or number)
    rows = ndi.binary_dilation(out, np.ones((1, 9), bool))
    lab2, n2 = ndi.label(rows)
    keep = np.zeros_like(out)
    for i, s in enumerate(ndi.find_objects(lab2)):
        if s[1].stop - s[1].start >= 18:
            keep[s] |= out[s] & (lab2[s] == i + 1)
    return keep


def classify(im_a, a, im_b, b, h):
    s = h.get('scale', 1.0)
    A = ink(im_a, a)
    B = _resize(ink(im_b, b), s)
    dy, dx = h['dy'], h['dx']
    # B placed in A's coordinates: B[y, x] -> A[y + dy, x + dx]
    y0, x0 = max(0, dy), max(0, dx)
    y1, x1 = min(A.shape[0], B.shape[0] + dy), min(A.shape[1], B.shape[1] + dx)
    r = {'kind': 'part', 'ident': None, 'same_title': None, 'same_text': None, 'offset': [dx, dy]}
    if y1 - y0 < 20 or x1 - x0 < 20:
        return r
    wa, wb = A[y0:y1, x0:x1], B[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    # ignore the frame lines themselves
    lines = lambda m: ndi.binary_opening(m, np.ones((1, 30), bool)) | ndi.binary_opening(m, np.ones((30, 1), bool))
    ca, cb = wa & ~ndi.binary_dilation(lines(wa), iterations=2), wb & ~ndi.binary_dilation(lines(wb), iterations=2)
    r['ident'] = _agree(ca, cb)
    cover = (y1 - y0) * (x1 - x0) / min(A.size, B.size)
    same_frame = abs(dx) <= 4 and abs(dy) <= 4 and abs(A.shape[0] - B.shape[0]) <= 0.04 * A.shape[0] and abs(A.shape[1] - B.shape[1]) <= 0.04 * A.shape[1]
    if r['ident'] is not None and r['ident'] >= 0.75:
        r['kind'] = 'whole' if same_frame else 'crop'
    if r['kind'] == 'whole':
        ta, tb = _text(wa), _text(wb)
        if ta.sum() + tb.sum() >= 60:
            r['same_text'] = _agree(ta, tb)
        # title strips above the two panels
        hh = int(0.22 * (a[3] - a[1]))
        sa = ink(im_a, (a[0], a[1] - hh, a[2], a[1] - 3))
        hb = int(0.22 * (b[3] - b[1]))
        sb = _resize(ink(im_b, (b[0], b[1] - hb, b[2], b[1] - 3)), s)
        hmin, wmin = min(sa.shape[0], sb.shape[0]), min(sa.shape[1], sb.shape[1])
        sa, sb = _text(sa[-hmin:, :wmin]), _text(sb[-hmin:, :wmin])
        if sa.sum() >= 40 and sb.sum() >= 40:
            best = 0
            for ox in range(-6, 7, 2):
                for oy in range(-4, 5, 2):
                    best = max(best, _agree(sa, np.roll(np.roll(sb, oy, 0), ox, 1)) or 0)
            r['same_title'] = best
    r['cover'] = float(cover)
    return r

"""Find repeated dot patterns inside one figure (flow cytometry panels).

The isolated dots of the whole figure are autocorrelated. A strong peak at a
non-zero shift means a group of dots reappears elsewhere in the figure: the
same events drawn in two panels, or a cloned patch inside one plot.

  python3 figscan.py FIGDIR OUT.json [--jobs 4]
"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panelmatch as pm


def scan(path, topk=6, min_dots=25, min_frac=0.6, min_spread=12):
    im = Image.open(path)
    pts, shape = pm.dots(im, border=0.0)
    out = {'file': os.path.basename(path), 'ndots': int(len(pts)), 'hits': []}
    if len(pts) < 2 * min_dots:
        return out
    R = pm._raster(pts, shape)
    Rd = ndi.maximum_filter(R, 3)
    cc = fftconvolve(Rd, R[::-1, ::-1], mode='full')
    cy, cx = shape[0] - 1, shape[1] - 1
    cc[:cy] = 0                      # keep one half-plane (dy >= 0)
    cc[cy, :cx + 8] = 0
    cc[cy:cy + 8, cx - 8:cx + 9] = 0  # near-zero shifts match a dot to its neighbours
    yi = np.round(pts[:, 0]).astype(int)
    xi = np.round(pts[:, 1]).astype(int)
    for _ in range(topk):
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape)
        M = cc[iy, ix]
        if M < min_dots:
            break
        cc[max(0, iy - 6):iy + 7, max(0, ix - 6):ix + 7] = 0
        dy, dx = iy - cy, ix - cx
        # dots of B (source) that land on a dot of A when moved by (dy, dx)
        ty, tx = yi + dy, xi + dx
        ok = (ty >= 0) & (ty < shape[0]) & (tx >= 0) & (tx < shape[1])
        hit = np.zeros(len(pts), bool)
        hit[ok] = Rd[ty[ok], tx[ok]] > 0
        if hit.sum() < min_dots:
            continue
        # group matched dots into compact clusters
        mm = pm._raster(pts[hit], shape)
        lab, n = ndi.label(ndi.maximum_filter(mm, 25))
        for k in range(1, n + 1):
            sel = hit & (lab[yi, xi] == k)
            if sel.sum() < min_dots:
                continue
            y0, y1, x0, x1 = yi[sel].min(), yi[sel].max(), xi[sel].min(), xi[sel].max()
            if y1 - y0 < min_spread or x1 - x0 < min_spread:
                continue
            if len(np.unique(yi[sel])) < 8 or len(np.unique(xi[sel])) < 8:
                continue
            inb = (yi >= y0) & (yi <= y1) & (xi >= x0) & (xi <= x1)
            inb2 = (yi >= y0 + dy) & (yi <= y1 + dy) & (xi >= x0 + dx) & (xi <= x1 + dx)
            frac = sel.sum() / max(inb.sum(), inb2.sum(), 1)
            if frac < min_frac:
                continue
            # the two boxes must not overlap much (else it is one cloud's own regularity)
            ov = max(0, (x1 - x0) - abs(dx)) * max(0, (y1 - y0) - abs(dy))
            # tick marks and gridlines: many matched dots share a row or a column
            ry = np.bincount(yi[sel]); rx = np.bincount(xi[sel])
            ty_ = max(6, 4 * sel.sum() / (y1 - y0 + 1)); tx_ = max(6, 4 * sel.sum() / (x1 - x0 + 1))
            aligned = (ry[ry >= ty_].sum() + rx[rx >= tx_].sum()) / sel.sum()
            # hatching and dither patterns: evenly spaced dots
            P = pts[sel]
            d2 = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1) if len(P) <= 1500 else None
            if d2 is not None:
                np.fill_diagonal(d2, 1e9)
                nn = np.sqrt(d2.min(1)); nncv = float(nn.std() / max(nn.mean(), 1e-6))
            else:
                nncv = 1.0
            out['hits'].append({'n': int(sel.sum()), 'frac': float(frac),
                                'aligned': float(aligned), 'nncv': nncv,
                                'boxfrac': float(max((x1 - x0) / shape[1], (y1 - y0) / shape[0])),
                                'dy': int(dy), 'dx': int(dx),
                                'src': [int(x0), int(y0), int(x1), int(y1)],
                                'dst': [int(x0 + dx), int(y0 + dy), int(x1 + dx), int(y1 + dy)],
                                'overlap': float(ov / max((x1 - x0) * (y1 - y0), 1)),
                                'score': float(sel.sum() * frac)})
    out['hits'].sort(key=lambda h: -h['score'])
    return out


def _safe(p):
    try:
        return scan(p)
    except Exception as e:
        return {'file': os.path.basename(p), 'error': str(e), 'hits': []}


if __name__ == '__main__':
    from multiprocessing import Pool
    d, outp = sys.argv[1], sys.argv[2]
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 4
    files = sorted(os.path.join(d, f) for f in os.listdir(d))
    with Pool(jobs) as P:
        res = list(P.imap_unordered(_safe, files, chunksize=4))
    json.dump(res, open(outp, 'w'))
    hits = [r for r in res if r['hits']]
    print('figures', len(res), 'with hits', len(hits), 'errors', sum('error' in r for r in res))

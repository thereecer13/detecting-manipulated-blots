"""Find flow cytometry dot plots in a figure, then compare them pairwise.

A flow plot here is a framed panel (axis lines at least on the left and
bottom) of roughly square shape that contains scattered single dots and at
least one of: a gate inside the frame (quadrant lines, rectangle, polygon)
or logarithmic tick marks. Bar charts (hatching forms a regular lattice),
UMAP maps and icons (no frame) are excluded.

  python3 facs_panels.py FIGDIR OUT.json [--jobs 3]
"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panelmatch as pm
import facsplot as fp

SC = [1.0, 0.8, 0.9, 1.1, 1.25]


def panel_dots(im, box, thr=60):
    """Isolated dots inside a panel box, without tick marks or other marks next to straight lines."""
    x0, y0, x1, y1 = box
    crop = im.crop((x0, y0, x1 + 1, y1 + 1))
    pts, shp = pm.dots(crop, border=0.04)
    dark = fp.ink_of(crop) > thr
    lines = ndi.binary_opening(dark, np.ones((1, 40), bool)) | ndi.binary_opening(dark, np.ones((40, 1), bool))
    nearline = ndi.binary_dilation(lines, iterations=3)
    if len(pts):
        pts = pts[~nearline[np.round(pts[:, 0]).astype(int), np.round(pts[:, 1]).astype(int)]]
    return pts, shp


def find_panels(im, thr=60):
    B = fp.ink_of(im)
    H, W = B.shape
    dark = B > thr
    L = 40
    hl = ndi.binary_opening(dark, np.ones((1, L), bool))
    vl = ndi.binary_opening(dark, np.ones((L, 1), bool))
    lab, n = ndi.label(hl | vl, structure=np.ones((3, 3)))
    out = []
    for i, s in enumerate(ndi.find_objects(lab)):
        y0, y1, x0, x1 = s[0].start, s[0].stop - 1, s[1].start, s[1].stop - 1
        w, h = x1 - x0, y1 - y0
        if w < 60 or h < 60 or w > 700 or h > 700 or not 0.6 <= w / h <= 1.7:
            continue
        comp = lab[s] == i + 1
        ch, cv = comp & hl[s], comp & vl[s]
        # axis lines: the outermost nearly complete lines (tick marks may stick out beyond them)
        colc, rowc = cv.mean(0), ch.mean(1)
        mw, mh = max(4, int(0.15 * w)), max(4, int(0.15 * h))
        lx = next((k for k in range(mw) if colc[k] > 0.75), None)
        by = next((k for k in range(mh) if rowc[-1 - k] > 0.75), None)
        if lx is None or by is None:
            continue
        rx = next((k for k in range(mw) if colc[-1 - k] > 0.75), None)
        ty = next((k for k in range(mh) if rowc[k] > 0.75), None)
        closed = rx is not None and ty is not None
        x0, y1 = x0 + lx, y1 - by
        x1 = x1 - (rx or 0)
        y0 = y0 + (ty or 0)
        w, h = x1 - x0, y1 - y0
        if w < 60 or h < 60:
            continue
        sub = (slice(y0, y1 + 1), slice(x0, x1 + 1))
        comp = lab[sub] == i + 1
        ch, cv = comp & hl[sub], comp & vl[sub]
        # flow plots are drawn on white paper; photographs and heat maps are not
        rgbmin = np.asarray(im.convert('RGB').crop((x0, y0, x1 + 1, y1 + 1))).min(2)
        white = float((rgbmin > 215).mean())
        if white < 0.45:
            continue
        m = 6
        ih, iv = ch[m:-m, m:-m], cv[m:-m, m:-m]
        gate_h = bool((ih.sum(1) > 0.3 * w).any())
        gate_v = bool((iv.sum(0) > 0.3 * h).any())
        crop = im.crop((x0, y0, x1 + 1, y1 + 1))
        pts, shp = panel_dots(im, [x0, y0, x1, y1])
        # a frame holding two or more separate inner frames (thin outlines) is a grid of small plots
        other = (hl | vl)[y0 + m:y1 - m, x0 + m:x1 - m] & ~(lab[y0 + m:y1 - m, x0 + m:x1 - m] == i + 1)
        l3, _ = ndi.label(other, structure=np.ones((3, 3)))
        sub = 0
        for k, t in enumerate(ndi.find_objects(l3)):
            hh, ww = t[0].stop - t[0].start, t[1].stop - t[1].start
            if hh > 0.15 * h and ww > 0.15 * w and (l3[t] == k + 1).mean() < 0.15:
                sub += 1
        if sub >= 2:
            continue
        if len(pts) < 30:
            continue
        # lattice test (hatched bars, dither): evenly spaced dots
        P = pts[:1200]
        d2 = ((P[:, None, :] - P[None, :, :]) ** 2).sum(-1)
        np.fill_diagonal(d2, 1e9)
        nn = np.sqrt(d2.min(1))
        nncv = float(nn.std() / max(nn.mean(), 1e-6))
        # polygon / rectangle gates: thin outlines inside the frame that are not lines of the frame
        D = dark[y0 + m:y1 - m, x0 + m:x1 - m] & ~(lab[y0 + m:y1 - m, x0 + m:x1 - m] == i + 1)
        poly = False
        l2, _ = ndi.label(D, structure=np.ones((3, 3)))
        for k, t in enumerate(ndi.find_objects(l2)):
            hh, ww = t[0].stop - t[0].start, t[1].stop - t[1].start
            if hh > 0.2 * h and ww > 0.2 * w and (l2[t] == k + 1).mean() < 0.12:
                poly = True
                break
        # log ticks just outside the bottom and left axes
        lg = 0
        band = dark[y1 + 1:y1 + 6, x0:x1 + 1]
        if band.size:
            lg = max(lg, fp.log_score(fp._ticks(band.sum(0), 2)))
        band = dark[y0:y1 + 1, max(0, x0 - 6):max(0, x0 - 1)]
        if band.size:
            lg = max(lg, fp.log_score(fp._ticks(band.sum(1), 2)))
        gate = gate_h or gate_v or poly
        # hatching: most dots sit at the same distance from their neighbour
        med = np.median(nn)
        lattice = float((np.abs(nn - med) <= 0.15 * med + 0.5).mean())
        if nncv < 0.35 or lattice > 0.6 or not (gate or lg >= 2):
            continue
        out.append({'box': [int(x0), int(y0), int(x1), int(y1)], 'closed': bool(closed),
                    'quadrant': gate_h and gate_v, 'gate_lines': gate_h or gate_v,
                    'gate_outline': poly, 'log_runs': int(lg), 'ndots': int(len(pts)),
                    'nncv': nncv, 'lattice': lattice, 'white': white, '_pts': (pts, shp)})
    return out


def scan(path):
    im = Image.open(path)
    ps = find_panels(im)
    res = {'file': os.path.basename(path), 'panels': [], 'pairs': []}
    def inside(a, b):   # a mostly inside b
        ix = max(0, min(a[2], b[2]) - max(a[0], b[0])) * max(0, min(a[3], b[3]) - max(a[1], b[1]))
        return ix > 0.5 * (a[2] - a[0]) * (a[3] - a[1])
    # a frame that holds other frames is a multi-panel container, not a plot
    ps = [p for p in ps if not any(q is not p and inside(q['box'], p['box']) for q in ps)]
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            r = pm.match_dots(ps[i]['_pts'], ps[j]['_pts'], scales=SC)
            if r['score'] >= 8:
                r.update(i=i, j=j)
                res['pairs'].append(r)
    for p in ps:
        p.pop('_pts')
        res['panels'].append(p)
    res['pairs'].sort(key=lambda r: -r['score'])
    return res


def _safe(p):
    try:
        return scan(p)
    except Exception as e:
        return {'file': os.path.basename(p), 'error': repr(e), 'panels': [], 'pairs': []}


if __name__ == '__main__':
    from multiprocessing import Pool
    d, outp = sys.argv[1], sys.argv[2]
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 3
    files = sorted(os.path.join(d, f) for f in os.listdir(d))
    with Pool(jobs) as P:
        res = list(P.imap_unordered(_safe, files, chunksize=4))
    json.dump(res, open(outp, 'w'))
    print('figures', len(res), 'with flow panels', sum(1 for r in res if r['panels']),
          'panels', sum(len(r['panels']) for r in res),
          'figures with a matching pair', sum(1 for r in res if r['pairs']),
          'errors', sum('error' in r for r in res))

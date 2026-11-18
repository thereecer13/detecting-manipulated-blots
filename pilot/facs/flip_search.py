"""Mirrored and rotated matches between flow-plot dots.

For every flow panel: does a patch of its isolated dots reappear inside the same panel mirrored
left-right, flipped top-bottom or rotated by 90, 180 or 270 degrees? For every pair of panels in one
figure: does one match the other after such a turn?

  python3 flip_search.py PANELS.json FIGDIR OUT.json [--jobs 2]
"""
import sys, os, json
import numpy as np
from PIL import Image
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panelmatch as pm
import facs_panels as fpn

FIGDIR = None


def turn(pts, shp, t):
    """Points (y, x) and shape after transform t."""
    H, W = shp
    y, x = pts[:, 0], pts[:, 1]
    if t == 'hflip':
        return np.stack([y, W - 1 - x], 1), (H, W)
    if t == 'vflip':
        return np.stack([H - 1 - y, x], 1), (H, W)
    if t == 'rot180':
        return np.stack([H - 1 - y, W - 1 - x], 1), (H, W)
    if t == 'rot90':
        return np.stack([x, H - 1 - y], 1), (W, H)
    if t == 'rot270':
        return np.stack([W - 1 - x, y], 1), (W, H)
    raise ValueError(t)


def run(x):
    out = []
    try:
        im = Image.open(os.path.join(FIGDIR, x['file'])).convert('RGB')
        D = [fpn.panel_dots(im, p['box']) for p in x['panels']]
        for i, (pts, shp) in enumerate(D):
            if len(pts) < 30:
                continue
            for t in ('hflip', 'vflip', 'rot180', 'rot90', 'rot270'):
                h = pm.match_dots((pts, shp), turn(pts, shp, t), scales=[1.0])
                if h['M'] - h['S'] >= 12 and h['M'] >= 20:
                    out.append(dict(h, file=x['file'], kind='within', i=i, j=i, turn=t))
        for i in range(len(D)):
            for j in range(i + 1, len(D)):
                if len(D[i][0]) < 20 or len(D[j][0]) < 20:
                    continue
                for t in ('hflip', 'vflip', 'rot180', 'rot90', 'rot270'):
                    h = pm.match_dots(D[i], turn(*D[j], t), scales=[1.0])
                    if h['M'] - h['S'] >= 12 and h['M'] >= 20:
                        out.append(dict(h, file=x['file'], kind='pair', i=i, j=j, turn=t))
    except Exception as e:
        out.append({'file': x['file'], 'error': repr(e)})
    return out


if __name__ == '__main__':
    panels, FIGDIR, outp = sys.argv[1:4]
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 2
    rows = [x for x in json.load(open(panels)) if x['panels']]
    with Pool(jobs) as P:
        res = [y for o in P.imap_unordered(run, rows, chunksize=4) for y in o]
    json.dump(res, open(outp, 'w'))
    print(len(rows), 'figures;', sum('M' in r for r in res), 'hits;', sum('error' in r for r in res), 'errors')

"""Cloned patches inside one flow plot, including dense regions (block matching on pixel texture).

The plot is cut into overlapping blocks. Blocks with fine texture are compared with all others; a clone
shows up as many blocks that each match a block at the same offset (or the same mirror / rotation) and
form one connected region.

  python3 patch_clone.py PANELS.json FIGDIR OUT.json [--jobs 2]
  python3 patch_clone.py --selftest PANELS.json FIGDIR [n]     # synthetic clones in real plots
"""
import sys, os, json, io, random
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

BS, ST = 12, 2            # block size, query stride
TURNS = {'same': lambda b: b, 'hflip': lambda b: b[:, :, ::-1], 'vflip': lambda b: b[:, ::-1], 'rot180': lambda b: b[:, ::-1, ::-1]}


def gray(im):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    return 0.5 * (255 - a.min(axis=2)) + 0.5 * (255 - a.mean(axis=2))


def blocks(g, st):
    hp = g - ndi.gaussian_filter(g, 2.0)
    dark = g > 60
    lines = ndi.binary_dilation(ndi.binary_opening(dark, np.ones((1, 30), bool)) | ndi.binary_opening(dark, np.ones((30, 1), bool)), iterations=2)
    H, W = g.shape
    ys, xs = np.mgrid[0:H - BS + 1:st, 0:W - BS + 1:st]
    ys, xs = ys.ravel(), xs.ravel()
    idx = (ys[:, None, None] + np.arange(BS)[None, :, None], xs[:, None, None] + np.arange(BS)[None, None, :])
    B = hp[idx]
    e = B.std(axis=(1, 2))
    ok = (e > 9) & (~lines[idx].any(axis=(1, 2)))
    B, ys, xs = B[ok], ys[ok], xs[ok]
    B = B - B.mean(axis=(1, 2), keepdims=True)
    B /= np.linalg.norm(B.reshape(len(B), -1), axis=1)[:, None, None] + 1e-6
    return B, ys, xs


_PROJ = np.linalg.qr(np.random.RandomState(0).randn(BS * BS, 24))[0].astype(np.float32)


def scan(im, min_blocks=8, thr=0.90):
    """Clone hypotheses, one per turn: dict(turn, n, compact, offset, src, dst, score), best first.

    Every block position of the plot is indexed (stride 1), so a copy is found at any offset; queries are
    the blocks on a coarser grid, in four orientations. Candidates from a 24-dimension projection are
    confirmed by the correlation of the full blocks."""
    g = gray(im)
    if g.shape[0] > 420 or g.shape[1] > 420:
        return []
    B, ys, xs = blocks(g, 1)
    out = []
    if len(B) < 200:
        return out
    flat = B.reshape(len(B), -1)
    tree = cKDTree(flat @ _PROJ)
    qi = np.nonzero((ys % ST == 0) & (xs % ST == 0))[0]
    for t, f in TURNS.items():
        q = np.ascontiguousarray(f(B[qi])).reshape(len(qi), -1)
        d, nn = tree.query(q @ _PROJ, k=6, distance_upper_bound=0.45)
        votes = {}
        for a in range(len(qi)):
            i = qi[a]
            for j in nn[a][np.isfinite(d[a])]:
                if abs(xs[j] - xs[i]) < BS and abs(ys[j] - ys[i]) < BS:
                    continue
                if float(q[a] @ flat[j]) < thr:
                    continue
                k = (int(xs[j] + xs[i]) if t in ('hflip', 'rot180') else int(xs[j] - xs[i]),
                     int(ys[j] + ys[i]) if t in ('vflip', 'rot180') else int(ys[j] - ys[i]))
                votes.setdefault(k, []).append((i, j))
        if t == 'same':      # a pair is found from both ends: fold opposite offsets together
            fold = {}
            for k, v in votes.items():
                kk = k if (k[1], k[0]) > (0, 0) else (-k[0], -k[1])
                fold.setdefault(kk, []).extend(v if kk == k else [(j, i) for i, j in v])
            votes = fold
        best = None
        for k, v in votes.items():
            src = {p[0] for p in v}
            if len(src) >= min_blocks and (best is None or len(src) > best[0]):
                best = (len(src), k, v)
        if best is None:
            continue
        n, k, tot = best
        si = np.array(sorted({p[0] for p in tot})); di = np.array(sorted({p[1] for p in tot}))
        m = np.zeros(g.shape, bool)   # the matched blocks must form one compact region, not a scatter
        for i in si:
            m[ys[i]:ys[i] + BS, xs[i]:xs[i] + BS] = True
        lab, nl = ndi.label(m)
        big = ndi.sum(m, lab, range(1, nl + 1)).max() / m.sum()
        box = lambda ii: [int(xs[ii].min()), int(ys[ii].min()), int(xs[ii].max() + BS), int(ys[ii].max() + BS)]
        out.append({'turn': t, 'n': int(n), 'compact': float(big), 'offset': list(k), 'src': box(si), 'dst': box(di),
                    'score': float(n * big)})
    return sorted(out, key=lambda h: -h['score'])


def _clone(im, rng, turn):
    """Paste a patch of the plot elsewhere in it (soft edge), re-save as JPEG. Returns image or None."""
    a = np.asarray(im.convert('RGB')).copy()
    g = gray(im)
    tex = ndi.uniform_filter((np.abs(g - ndi.gaussian_filter(g, 2)) > 12).astype(np.float32), 25)
    H, W = g.shape
    s = rng.randint(26, 44)
    cand = np.argwhere(tex[s // 2:H - s // 2, s // 2:W - s // 2] > 0.25)
    if len(cand) < 50:
        return None
    for _ in range(30):
        y0, x0 = cand[rng.randrange(len(cand))]
        y1, x1 = cand[rng.randrange(len(cand))]
        if abs(y1 - y0) >= s or abs(x1 - x0) >= s:
            p = a[y0:y0 + s, x0:x0 + s].copy()
            p = {'same': p, 'hflip': p[:, ::-1], 'vflip': p[::-1], 'rot180': p[::-1, ::-1]}[turn]
            a[y1:y1 + s, x1:x1 + s] = p
            buf = io.BytesIO(); Image.fromarray(a).save(buf, 'JPEG', quality=85); buf.seek(0)
            return Image.open(buf).convert('RGB')
    return None


def run(x):
    out = []
    try:
        im = Image.open(os.path.join(FIGDIR, x['file'])).convert('RGB')
        for k, p in enumerate(x['panels']):
            b = p['box']
            hs = scan(im.crop((b[0], b[1], b[2] + 1, b[3] + 1)))
            if hs:
                out.append({'file': x['file'], 'panel': k, 'box': b, 'hits': hs[:2]})
    except Exception as e:
        out.append({'file': x['file'], 'error': repr(e)})
    return out


FIGDIR = None
if __name__ == '__main__':
    if sys.argv[1] == '--selftest':
        panels, FIGDIR = sys.argv[2:4]; n = int(sys.argv[4]) if len(sys.argv) > 4 else 120
        rng = random.Random(1)
        rows = [(x['file'], p['box']) for x in json.load(open(panels)) for p in x['panels']]
        rng.shuffle(rows)
        res = {t: [0, 0] for t in TURNS}; clean = []; done = 0
        for f, b in rows:
            if done >= n:
                break
            im = Image.open(os.path.join(FIGDIR, f)).convert('RGB').crop((b[0], b[1], b[2] + 1, b[3] + 1))
            t = list(TURNS)[done % 4]
            forged = _clone(im, rng, t)
            if forged is None:
                continue
            done += 1
            h0 = scan(im); clean.append(h0[0]['score'] if h0 else 0)
            h1 = scan(forged)
            res[t][1] += 1
            res[t][0] += bool(h1) and h1[0]['score'] > (h0[0]['score'] if h0 else 0) + 5 and h1[0]['turn'] == t
        c = np.array(clean)
        print('found / planted by turn:', res)
        print('clean plots: best score percentiles 50/90/95/99:', np.percentile(c, [50, 90, 95, 99]).round(1), 'share with any hit', float((c > 0).mean()))
    else:
        from multiprocessing import Pool
        panels, FIGDIR, outp = sys.argv[1:4]
        jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else 2
        rows = [x for x in json.load(open(panels)) if x['panels']]
        with Pool(jobs) as P:
            res = [y for o in P.imap_unordered(run, rows, chunksize=4) for y in o]
        json.dump(res, open(outp, 'w'))
        print(len(rows), 'figures;', sum('hits' in r for r in res), 'panels with a hit;', sum('error' in r for r in res), 'errors')

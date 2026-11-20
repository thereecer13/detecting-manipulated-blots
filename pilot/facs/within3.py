"""Within-plot clone search by autocorrelation of the dot mask.

A patch of events copied to another place in the same plot makes the plot's small-dot mask coincide with
itself at one exact offset. The autocorrelation of the mask then has a sharp spike at that offset, standing
above the smooth background that the overall shape of the event cloud produces.
  scan(rgb) -> list of hits {dx, dy, z, excess, n, box, boxfrac}
  python3 within3.py CHUNKDIR      (writes CHUNKDIR/within3.json)
"""
import json, sys
import numpy as np, cv2
MAXBLOB = 30          # ink components larger than this (px) are text, lines or dense cloud, not single events
def dot_mask(rgb, border=0.05):
    g = rgb.min(2) if rgb.ndim == 3 else rgb
    ink = (g < 150).astype(np.uint8); H, W = ink.shape
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, 8)
    ok = np.zeros(n, bool)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        ok[i] = a <= MAXBLOB and w <= 8 and h <= 8
    m = ok[lab]; by, bx = int(H * border), int(W * border)
    m[:by] = False; m[H - by:] = False; m[:, :bx] = False; m[:, W - bx:] = False
    return m, int(ok.sum())
def scan(rgb, min_shift=8, topk=3, zmin=6.0):
    m, nd = dot_mask(rgb); H, W = m.shape
    if nd < 40: return {'ndots': nd, 'hits': []}
    f = np.fft.rfft2(m.astype(np.float32), s=(2 * H, 2 * W)); A = np.fft.irfft2(f * np.conj(f), s=(2 * H, 2 * W))
    A = np.fft.fftshift(A); cy, cx = H, W                      # A[cy+dy, cx+dx] = coincidences at shift (dx, dy)
    A = A[cy - H // 2:cy + H // 2, cx - W // 2:cx + W // 2]; oy, ox = H // 2, W // 2
    bg = cv2.medianBlur(A.astype(np.float32), 5); bg = cv2.blur(bg, (9, 9))
    E = A - bg; Z = E / np.sqrt(np.maximum(bg, 1.0))
    yy, xx = np.mgrid[:A.shape[0], :A.shape[1]]; Z[np.hypot(yy - oy, xx - ox) < min_shift] = 0; Z[:oy] = 0   # half plane
    hits = []
    for _ in range(topk):
        iy, ix = np.unravel_index(np.argmax(Z), Z.shape); z = float(Z[iy, ix])
        if z < zmin: break
        dy, dx = int(iy - oy), int(ix - ox)
        Z[max(0, iy - 4):iy + 5, max(0, ix - 4):ix + 5] = 0
        a = m[max(0, -dy):H - max(0, dy), max(0, -dx):W - max(0, dx)]; b = m[max(0, dy):H - max(0, -dy), max(0, dx):W - max(0, -dx)]
        co = (a & b).astype(np.uint8); n, lab, st, cen = cv2.connectedComponentsWithStats(co, 8)
        if n - 1 < 8: continue
        c = cen[1:]; x0, x1 = np.percentile(c[:, 0], [10, 90]); y0, y1 = np.percentile(c[:, 1], [10, 90])
        box = [int(x0 + max(0, -dx)), int(y0 + max(0, -dy)), int(x1 + max(0, -dx)), int(y1 + max(0, -dy))]
        # one compact cluster? group coinciding dots that lie within ~14 px of each other
        big = cv2.dilate(co, np.ones((15, 15), np.uint8)); k2, lab2 = cv2.connectedComponents(big, 8)
        cl = lab2[np.clip(c[:, 1].round().astype(int), 0, co.shape[0] - 1), np.clip(c[:, 0].round().astype(int), 0, co.shape[1] - 1)]
        top = np.bincount(cl).argmax(); pts = c[cl == top]; share = len(pts) / len(c); elong = 0.0
        if len(pts) >= 5:
            ev = np.sqrt(np.maximum(np.linalg.eigvalsh(np.cov(pts.T)), 0)); elong = float(ev[0] / max(ev[1], 1e-6))
        hits.append({'dx': dx, 'dy': dy, 'z': z, 'excess': float(E[iy, ix]), 'n': int(n - 1), 'box': box,
                     'cluster_n': int(len(pts)), 'cluster_share': float(share), 'elong': elong,
                     'boxfrac': float(max(x1 - x0, 1) * max(y1 - y0, 1) / (H * W)),
                     'lattice': float(np.sort(Z.ravel())[-20:].mean() / z)})
    return {'ndots': nd, 'hits': hits}
if __name__ == '__main__':
    from PIL import Image
    from multiprocessing import Pool
    D = sys.argv[1]
    def run(x):
        out = []
        try:
            im = np.asarray(Image.open(D + '/figs/' + x['file']).convert('RGB'))
            for k, p in enumerate(x['panels']):
                b = p['box']; r = scan(im[b[1]:b[3] + 1, b[0]:b[2] + 1])
                if r['hits']: out.append({'file': x['file'], 'panel': k, 'box': b, 'ndots': r['ndots'], 'hits': r['hits']})
        except Exception as e: out.append({'file': x['file'], 'error': repr(e)})
        return out
    r = [x for x in json.load(open(D + '/panels.json')) if x['panels']]
    with Pool(2) as P: res = [y for o in P.imap_unordered(run, r, chunksize=4) for y in o]
    json.dump(res, open(D + '/within3.json', 'w')); print(len(res), 'panels with a hit')

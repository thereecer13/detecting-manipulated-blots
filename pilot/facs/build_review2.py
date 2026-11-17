"""Review items for matching flow-plot panel pairs found by facs_panels.py.

  python3 build_review2.py PANELS.json FIGS.jsonl FIGDIR OUTDIR [--n 40] [--min 8]
"""
import sys, os, json
from PIL import Image, ImageDraw
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panelmatch as pm


def matched_dots(im, a, b, h, im_b=None):
    """Coinciding dots as figure coordinates: (points in A, points in B)."""
    pa, sa = pm.dots(im.crop((a[0], a[1], a[2] + 1, a[3] + 1)), border=0.04)
    pb, sb = pm.dots((im_b or im).crop((b[0], b[1], b[2] + 1, b[3] + 1)), border=0.04)
    if not len(pa) or not len(pb):
        return np.zeros((0, 2)), np.zeros((0, 2))
    Am = pm._raster(pa, sa)
    idx = ndi.distance_transform_edt(Am == 0, return_distances=False, return_indices=True)
    t = np.round(pb * h['scale']).astype(int) + [h['dy'], h['dx']]
    ok = (t[:, 0] >= 0) & (t[:, 0] < sa[0]) & (t[:, 1] >= 0) & (t[:, 1] < sa[1])
    qa, qb = [], []
    for k in np.where(ok)[0]:
        y, x = t[k]
        ny, nx = idx[0][y, x], idx[1][y, x]
        if abs(ny - y) <= 1 and abs(nx - x) <= 1:
            qa.append((ny + a[1], nx + a[0])); qb.append((pb[k][0] + b[1], pb[k][1] + b[0]))
    return np.array(qa).reshape(-1, 2), np.array(qb).reshape(-1, 2)


def highlight(im, box, pts, pad, target=340):
    """Enlarged crop with every coinciding dot ringed and their region outlined."""
    x0, y0 = box[0] - pad, box[1] - pad
    c = im.crop((x0, y0, box[2] + pad, box[3] + pad))
    s = min(4, target / max(c.size))
    c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
    d = ImageDraw.Draw(c)
    r = max(3, int(2.2 * s))
    for y, x in pts:
        cx, cy = (x - x0 + 0.5) * s, (y - y0 + 0.5) * s
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 170, 0), width=1)
    if len(pts) >= 5:
        ys, xs = pts[:, 0], pts[:, 1]
        bb = [np.percentile(xs, 3), np.percentile(ys, 3), np.percentile(xs, 97), np.percentile(ys, 97)]
        d.rectangle([(bb[0] - x0) * s - r - 2, (bb[1] - y0) * s - r - 2, (bb[2] - x0) * s + r + 2, (bb[3] - y0) * s + r + 2],
                    outline=(255, 140, 0), width=2)
    return c


def main():
    scan, meta, figdir, out = sys.argv[1:5]
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 40
    mn = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 8
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
    os.makedirs(out, exist_ok=True)
    M = {}
    for l in open(meta):
        d = json.loads(l)
        if 'file' in d:
            M[d['file']] = d
    rows = []
    for r in json.load(open(scan)):
        if r['pairs'] and r['pairs'][0]['score'] >= mn:
            rows.append((r['pairs'][0]['score'], r))
    rows.sort(key=lambda t: -t[0])
    items, key, papers = [], {}, set()
    for sc, r in rows:
        f = r['file']; m = M.get(f, {}); h = r['pairs'][0]
        if m.get('pmcid') in papers or (only and m.get('pmcid') not in only):
            continue
        papers.add(m.get('pmcid'))
        idx = 'G%02d' % len(items)
        a, b = r['panels'][h['i']]['box'], r['panels'][h['j']]['box']
        im = Image.open(os.path.join(figdir, f)).convert('RGB')
        box = im.copy(); d = ImageDraw.Draw(box); w = max(3, max(im.size) // 300)
        for bb, col in ((a, (255, 0, 0)), (b, (0, 90, 255))):
            d.rectangle([bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6], outline=col, width=w)
        box.thumbnail((560, 560), Image.LANCZOS)
        p1 = os.path.join(out, idx + '_fig.png'); box.save(p1)
        pad = 8
        ca = im.crop((a[0] - pad, a[1] - pad, a[2] + pad, a[3] + pad))
        if h['scale'] == 1.0:   # same window, shifted so that the matching dots coincide
            ox, oy = b[0] - h['dx'], b[1] - h['dy']
            cb = im.crop((ox - pad, oy - pad, ox + (a[2] - a[0]) + pad, oy + (a[3] - a[1]) + pad))
        else:
            cb = im.crop((b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad))
        s = min(4, 340 / max(ca.size))
        sz = (max(1, int(ca.width * s)), max(1, int(ca.height * s)))
        ca, cb = ca.resize(sz, Image.LANCZOS), cb.resize(sz, Image.LANCZOS)
        pair = Image.new('RGB', (sz[0] * 2 + 12, sz[1]), 'white')
        pair.paste(ca, (0, 0)); pair.paste(cb, (sz[0] + 12, 0))
        p2 = os.path.join(out, idx + '_pair.png'); pair.save(p2)
        qa, qb = matched_dots(im, a, b, h)
        ha, hb = highlight(im, a, qa, pad), highlight(im, b, qb, pad)
        hl = Image.new('RGB', (ha.width + hb.width + 12, max(ha.height, hb.height)), 'white')
        hl.paste(ha, (0, 0)); hl.paste(hb, (ha.width + 12, 0))
        p4 = os.path.join(out, idx + '_dots.png'); hl.save(p4)
        p3 = os.path.join(out, idx + '_ab.gif')
        ca.convert('P', palette=Image.ADAPTIVE, colors=64).save(
            p3, save_all=True, append_images=[cb.convert('P', palette=Image.ADAPTIVE, colors=64)],
            duration=700, loop=0)
        cap = m.get('caption', '')
        nmin = min(h['na'], h['nb'])
        label = ('%s — %d single dots coincide (%d%% of the isolated dots in the sparser plot; best chance '
                 'alignment gives %d). %s %s. Caption: %s') % (
            idx, h['M'], round(100 * min(1, h['M'] / max(nmin, 1))), h['S'], m.get('pmcid', ''),
            m.get('label', ''), cap[:500] + ('…' if len(cap) > 500 else ''))
        items.append({'id': idx, 'label': label, 'images': [
            {'path': p1, 'caption': 'Whole figure: A red, B blue', 'color': True},
            {'path': p2, 'caption': 'A (left) and B (right), enlarged', 'color': True},
            {'path': p4, 'caption': 'Coinciding dots ringed in green; orange box = region they cover', 'color': True},
            {'path': p3, 'caption': 'A and B alternating', 'color': True}]})
        key[idx] = {'file': f, 'a': a, 'b': b, 'match': h, 'pmcid': m.get('pmcid'), 'doi': m.get('doi'),
                    'title': m.get('title'), 'citation': m.get('citation'), 'fig': m.get('label'),
                    'license': m.get('license'), 'retracted': m.get('retracted')}
        if len(items) >= n:
            break
    json.dump(items, open(os.path.join(out, 'items.json'), 'w'))
    json.dump(key, open(os.path.join(out, 'key.json'), 'w'), indent=1)
    print(len(items), 'items from', len(rows), 'figures')


if __name__ == '__main__':
    main()

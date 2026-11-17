"""Review items for matching flow-plot panel pairs found by facs_panels.py.

  python3 build_review2.py PANELS.json FIGS.jsonl FIGDIR OUTDIR [--n 40] [--min 8]
"""
import sys, os, json
from PIL import Image, ImageDraw


def main():
    scan, meta, figdir, out = sys.argv[1:5]
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 40
    mn = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 8
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
        if m.get('pmcid') in papers:
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

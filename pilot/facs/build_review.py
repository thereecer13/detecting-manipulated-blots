"""Build review items for figures where figscan.py found a repeated dot pattern.

  python3 build_review.py SCAN.json FIGS.jsonl FIGDIR OUTDIR [--n 40]
Writes OUTDIR/items.json (for make_review_html.py) and OUTDIR/key.json.
"""
import sys, os, json
from PIL import Image, ImageDraw


def main():
    scan, meta, figdir, out = sys.argv[1:5]
    n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 40
    os.makedirs(out, exist_ok=True)
    M = {}
    for l in open(meta):
        d = json.loads(l)
        if 'file' in d:
            M[d['file']] = d
    rows = []
    for r in json.load(open(scan)):
        hs = [h for h in r['hits'] if h['overlap'] < 0.3 and h['aligned'] < 0.6
              and h['nncv'] > 0.35 and h['boxfrac'] < 0.5]
        if hs:
            rows.append((hs[0]['score'], r['file'], hs[0]))
    rows.sort(key=lambda t: -t[0])
    items, key, papers = [], {}, set()
    for sc, f, h in rows:
        m = M.get(f, {})
        if m.get('pmcid') in papers:      # one figure per paper
            continue
        papers.add(m.get('pmcid'))
        idx = 'F%02d' % len(items)
        im = Image.open(os.path.join(figdir, f)).convert('RGB')
        box = im.copy()
        d = ImageDraw.Draw(box)
        w = max(3, max(im.size) // 300)
        for b, col, t in ((h['src'], (255, 0, 0), 'A'), (h['dst'], (0, 90, 255), 'B')):
            d.rectangle([b[0] - 8, b[1] - 8, b[2] + 8, b[3] + 8], outline=col, width=w)
        box.thumbnail((560, 560), Image.LANCZOS)
        p1 = os.path.join(out, idx + '_fig.png'); box.save(p1)
        pad = 10
        ca = im.crop((h['src'][0] - pad, h['src'][1] - pad, h['src'][2] + pad, h['src'][3] + pad))
        cb = im.crop((h['dst'][0] - pad, h['dst'][1] - pad, h['dst'][2] + pad, h['dst'][3] + pad))
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
        label = '%s — %d of the dots repeat (%.0f%% of those in the boxed area). %s %s. Caption: %s' % (
            idx, h['n'], 100 * h['frac'], m.get('pmcid', ''), m.get('label', ''),
            cap[:500] + ('…' if len(cap) > 500 else ''))
        items.append({'id': idx, 'label': label, 'images': [
            {'path': p1, 'caption': 'Whole figure: A red, B blue', 'color': True},
            {'path': p2, 'caption': 'A (left) and B (right), enlarged', 'color': True},
            {'path': p3, 'caption': 'A and B alternating', 'color': True}]})
        key[idx] = {'file': f, 'hit': h, 'pmcid': m.get('pmcid'), 'doi': m.get('doi'),
                    'title': m.get('title'), 'citation': m.get('citation'), 'fig': m.get('label'),
                    'license': m.get('license'), 'retracted': m.get('retracted')}
        if len(items) >= n:
            break
    json.dump(items, open(os.path.join(out, 'items.json'), 'w'))
    json.dump(key, open(os.path.join(out, 'key.json'), 'w'), indent=1)
    print(len(items), 'items;', len(rows), 'figures with a non-overlapping hit')


if __name__ == '__main__':
    main()

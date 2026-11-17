"""Review items for flow-plot pairs matched across figures of one paper (cross_fig.py output).

  python3 build_review3.py CROSS.json FIGS.jsonl FIGDIR OUTDIR [--min 20]
"""
import sys, os, json
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_review2 as b2


def boxed(im, bb, col):
    c = im.copy(); d = ImageDraw.Draw(c)
    d.rectangle([bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6], outline=col, width=max(3, max(im.size) // 300))
    c.thumbnail((1000, 1000), Image.LANCZOS)
    return c


def main():
    cross, meta, figdir, out = sys.argv[1:5]
    mn = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 20
    os.makedirs(out, exist_ok=True)
    M = {}
    for l in open(meta):
        d = json.loads(l)
        if 'file' in d:
            M[d['file']] = d
    rows = sorted([r for r in json.load(open(cross)) if 'score' in r and r['M'] - r['S'] >= mn],
                  key=lambda r: -(r['M'] - r['S']))
    items, key = [], {}
    for h in rows:
        idx = 'X%02d' % len(items)
        ia = Image.open(os.path.join(figdir, h['fa'])).convert('RGB')
        ib = Image.open(os.path.join(figdir, h['fb'])).convert('RGB')
        p1 = os.path.join(out, idx + '_figA.png'); boxed(ia, h['a'], (255, 0, 0)).save(p1)
        p2 = os.path.join(out, idx + '_figB.png'); boxed(ib, h['b'], (0, 90, 255)).save(p2)
        qa, qb = b2.matched_dots(ia, h['a'], h['b'], h, im_b=ib)
        ha, hb = b2.highlight(ia, h['a'], qa, 8), b2.highlight(ib, h['b'], qb, 8)
        hb = hb.resize((max(1, int(hb.width * ha.height / hb.height)), ha.height), Image.LANCZOS)
        hl = Image.new('RGB', (ha.width + hb.width + 12, ha.height), 'white')
        hl.paste(ha, (0, 0)); hl.paste(hb, (ha.width + 12, 0))
        p3 = os.path.join(out, idx + '_dots.png'); hl.save(p3)
        ca = b2.highlight(ia, h['a'], [], 8); cb = b2.highlight(ib, h['b'], [], 8).resize(ca.size, Image.LANCZOS)
        p4 = os.path.join(out, idx + '_ab.gif')
        ca.convert('P', palette=Image.ADAPTIVE, colors=64).save(
            p4, save_all=True, append_images=[cb.convert('P', palette=Image.ADAPTIVE, colors=64)], duration=700, loop=0)
        ma, mb = M.get(h['fa'], {}), M.get(h['fb'], {})
        label = ('%s — %s: %s (A) and %s (B). %d single dots coincide; best chance alignment gives %d%s. '
                 'Caption A: %s… Caption B: %s…') % (
            idx, h['pmcid'], ma.get('label', ''), mb.get('label', ''), h['M'], h['S'],
            '' if h['scale'] == 1.0 else '; B is drawn at %.0f%% of the size of A' % (100 / h['scale']),
            ma.get('caption', '')[:350], mb.get('caption', '')[:350])
        items.append({'id': idx, 'label': label, 'images': [
            {'path': p1, 'caption': 'Figure with plot A (red)', 'color': True},
            {'path': p2, 'caption': 'Figure with plot B (blue)', 'color': True},
            {'path': p3, 'caption': 'A (left) and B (right): coinciding dots ringed in green; orange box = region they cover', 'color': True},
            {'path': p4, 'caption': 'A and B alternating (B resized to A)', 'color': True}]})
        key[idx] = {k: h[k] for k in ('pmcid', 'fa', 'fb', 'a', 'b', 'M', 'S', 'scale', 'dx', 'dy')}
        key[idx].update(doi=ma.get('doi'), title=ma.get('title'), citation=ma.get('citation'))
    json.dump(items, open(os.path.join(out, 'items.json'), 'w'))
    json.dump(key, open(os.path.join(out, 'key.json'), 'w'), indent=1)
    print(len(items), 'items')


if __name__ == '__main__':
    main()

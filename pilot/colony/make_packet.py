"""Build a colony review packet. Usage: make_packet.py papers.jsonl spec.json outdir
spec = [{"id","pmcid","label"}]; writes outdir/items.json plus images."""
import json, sys, os, cv2, numpy as np
papers, spec, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
recs = {}
for l in open(papers):
    r = json.loads(l)
    if r.get('hits'): recs[r['pmcid']] = r
items = []
for s in json.load(open(spec)):
    r = recs[s['pmcid']]; h = r['hits'][s.get('hit', 0)]; imgs = []; ts = []
    for k in 'ab':
        im = cv2.imread(h[k]['file']); x, y, rr = h[k]['xyr']; p = int(rr * 1.12)
        ts.append(cv2.resize(im[max(0, y-p):y+p, max(0, x-p):x+p], (480, 480), interpolation=cv2.INTER_CUBIC))
    p0 = f"{out}/{s['id']}_pair.png"; cv2.imwrite(p0, np.hstack([ts[0], np.full((480, 16, 3), 255, np.uint8), ts[1]]))
    imgs.append({"path": p0, "caption": "The two plates enlarged", "color": "#c00"})
    for f in sorted({h[k]['file'] for k in 'ab'}):
        im = cv2.imread(f); pts = [h[k]['xyr'] for k in 'ab' if h[k]['file'] == f]
        for x, y, rr in pts: cv2.circle(im, (x, y), rr + 3, (0, 0, 255), 2)
        m = max(q[2] for q in pts) * 4
        x0 = max(0, min(q[0] for q in pts) - m); x1 = max(q[0] for q in pts) + m
        y0 = max(0, min(q[1] for q in pts) - m); y1 = max(q[1] for q in pts) + m
        c = im[y0:y1, x0:x1]; sc = min(3, 1500 / max(c.shape[:2]))
        p1 = f"{out}/{s['id']}_{os.path.basename(f)}.png"
        cv2.imwrite(p1, cv2.resize(c, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC))
        imgs.append({"path": p1, "caption": "Figure region with the plate(s) circled"})
    items.append({"id": s['id'], "label": f"{r['pmcid']}, {r['journal']} {r['year']}, doi:{r['doi']}. {s['label']}", "images": imgs})
json.dump(items, open(f"{out}/items.json", 'w'))
print(len(items))

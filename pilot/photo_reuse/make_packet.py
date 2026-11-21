"""Build a review packet from chosen hits.  make_packet.py OUTDIR spec.json packetdir
spec = [{"id", "pmcid", "hits": [k, ...] (index into that paper's hits list), "label"}]
For each hit: the two matched regions enlarged side by side (a mirrored copy is added when the match is
mirrored), then each figure region in wide context with the match boxed. Writes packetdir/items.json."""
import json, sys, os
from pathlib import Path
import cv2
import numpy as np
out, spec, pk = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
os.makedirs(pk, exist_ok=True)
recs = {}
for l in (out / "papers.jsonl").open():
    r = json.loads(l)
    if r["hits"]: recs[r["pmcid"]] = r


def region(im, box, pad, side):
    x0, y0, x1, y1 = box; p = int(pad * max(x1 - x0, y1 - y0))
    X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(im.shape[1], x1 + p), min(im.shape[0], y1 + p)
    c = im[Y0:Y1, X0:X1].copy()
    if pad > 0.2: cv2.rectangle(c, (x0 - X0, y0 - Y0), (x1 - X0, y1 - Y0), (0, 0, 255), 2)
    s = side / max(c.shape[:2])
    return cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)


def side_by_side(ts):
    H = max(t.shape[0] for t in ts); row = []
    for t in ts:
        row += [np.vstack([t, np.full((H - t.shape[0], t.shape[1], 3), 255, np.uint8)]), np.full((H, 16, 3), 255, np.uint8)]
    return np.hstack(row[:-1])


items = []
for s in json.load(open(spec)):
    r = recs[s["pmcid"]]; imgs = []
    for n, k in enumerate(s["hits"]):
        h = r["hits"][k]; A = cv2.imread(str(out / "figs" / h["a"])); B = cv2.imread(str(out / "figs" / h["b"]))
        ta, tb = region(A, h["abox"], 0.0, 520), region(B, h["bbox"], 0.0, 520)
        cap = "The two matched regions enlarged"
        ts = [ta, tb]
        if h["mirrored"]: ts = [ta, ta[:, ::-1], tb]; cap = "Left region as published, the same region mirrored, and the right region as published"
        p0 = f"{pk}/{s['id']}_{n}_pair.png"; cv2.imwrite(p0, side_by_side(ts)); imgs.append({"path": p0, "caption": cap, "color": True})
        p1 = f"{pk}/{s['id']}_{n}_ctx.png"; cv2.imwrite(p1, side_by_side([region(A, h["abox"], s.get("pad", 1.0), 760), region(B, h["bbox"], s.get("pad", 1.0), 760)]))
        imgs.append({"path": p1, "caption": "Where each region sits in its figure (boxed)", "color": True})
    items.append({"id": s["id"], "label": f"{r['pmcid']}, {r['journal']} {r['year']}" + (f", doi:{r['doi']}" if r.get("doi") else "") + f". {s['label']}", "images": imgs})
json.dump(items, open(f"{pk}/items.json", "w")); print(len(items))

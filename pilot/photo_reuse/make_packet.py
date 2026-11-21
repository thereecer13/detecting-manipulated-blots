"""Build a review packet from chosen hits.

    python3 make_packet.py OUTDIR spec.json PACKETDIR      ->  PACKETDIR/items.json and images

spec.json is a list of items:
  {"id": "Q00", "pmcid": "PMC...",
   "what": "which panels show the same image, with their labels",
   "why":  "why those panels should be different images, and where that comes from
            (panel labels, caption, main text / Methods)",
   "hits": [0, 1],            # indexes into the paper's hits list in OUTDIR/papers.jsonl, and / or
   "pairs": [{"a": "file", "abox": [x0, y0, x1, y1], "b": "file", "bbox": [...], "mirrored": false, "rot180": false, "vflip": false, "note": "..."}],
   "extra": [{"path": "...", "caption": "..."}],        # further images to show
   "pad": 1.0}

Every item must carry "why": a candidate goes to review only with an argument for why the two
images should not be the same, read from the figure labels, the caption and, where those do not
settle it, the main text (see paper_text.py).

Boxes: for "hits" the box is the whole area in which the two images agree (photo_dupes.full_extent),
not the bounding box of the matched keypoints, which is usually too small. Give "pairs" by hand
when the automatic box is wrong (for example a grid of look-alike panels).
For each pair the packet shows the two regions enlarged side by side (plus a mirrored copy when the
match is mirrored) and each region boxed in its figure.
"""
import json, sys, os
from pathlib import Path
import cv2
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import photo_dupes as P

out, spec, pk = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
os.makedirs(pk, exist_ok=True)
recs = {}
for l in (out / "papers.jsonl").open():
    r = json.loads(l); recs[r["pmcid"]] = r
COL = [(0, 0, 255), (255, 120, 0), (0, 170, 0), (200, 0, 200), (0, 170, 220), (120, 120, 0)]


def region(im, box, side):
    x0, y0, x1, y1 = box; c = im[y0:y1, x0:x1]; s = side / max(c.shape[:2])
    return cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)


def side_by_side(ts, gap=16):
    H = max(t.shape[0] for t in ts); row = []
    for t in ts:
        row += [np.vstack([t, np.full((H - t.shape[0], t.shape[1], 3), 255, np.uint8)]), np.full((H, gap, 3), 255, np.uint8)]
    return np.hstack(row[:-1])


def context(path, boxes, pad, side=900):
    """The figure around the given boxes [(box, colour, tag)], boxes drawn."""
    im = cv2.imread(str(path)); x0 = min(b[0][0] for b in boxes); y0 = min(b[0][1] for b in boxes); x1 = max(b[0][2] for b in boxes); y1 = max(b[0][3] for b in boxes)
    p = int(pad * max(x1 - x0, y1 - y0)) + 20
    X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(im.shape[1], x1 + p), min(im.shape[0], y1 + p)
    s = side / max(X1 - X0, Y1 - Y0); c = cv2.resize(im[Y0:Y1, X0:X1], None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    for (bx0, by0, bx1, by1), col, tag in boxes:
        q0 = (int((bx0 - X0) * s), int((by0 - Y0) * s)); q1 = (int((bx1 - X0) * s), int((by1 - Y0) * s))
        cv2.rectangle(c, q0, q1, col, 3)
        if tag:      # small tag in the box's top-left corner: panel labels outside the box stay readable,
            #          and the enlarged pair images show the whole region without it
            cv2.rectangle(c, (q0[0], q0[1]), (q0[0] + 12 * len(tag) + 8, q0[1] + 20), col, -1)
            cv2.putText(c, tag, (q0[0] + 4, q0[1] + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return c


items = []
for s in json.load(open(spec)):
    if not s.get("why", "").strip(): raise SystemExit(f"{s['id']}: no 'why' (the argument for why the images should differ)")
    r = recs[s["pmcid"]]; pairs = []
    for k in s.get("hits", []):
        h = r["hits"][k]; fa, fb = out / "figs" / h["a"], out / "figs" / h["b"]
        abox, bbox, share = P.full_extent(fa, fb, h)
        pairs.append({"a": h["a"], "b": h["b"], "abox": abox, "bbox": bbox, "mirrored": h["mirrored"], "note": ""})
    pairs += s.get("pairs", [])
    imgs = []; byfig = {}
    for n, p in enumerate(pairs):
        A = cv2.imread(str(out / "figs" / p["a"])); B = cv2.imread(str(out / "figs" / p["b"])); tag = chr(65 + n) if len(pairs) > 1 else ""
        ta, tb = region(A, p["abox"], 560), region(B, p["bbox"], 560); ts = [ta, tb]
        cap = (f"Pair {tag}: " if tag else "") + "the two matching regions enlarged" + (f" ({p['note']})" if p.get("note") else "")
        if p.get("rot180"): ts = [ta, cv2.rotate(tb, cv2.ROTATE_180), tb]; cap = (f"Pair {tag}: " if tag else "") + "first region as published, the second region turned 180 degrees, and the second region as published" + (f" ({p['note']})" if p.get("note") else "")
        if p.get("vflip"): ts = [ta, ta[::-1], tb]; cap = (f"Pair {tag}: " if tag else "") + "first region as published, the same region flipped top to bottom, and the second region as published" + (f" ({p['note']})" if p.get("note") else "")
        if p.get("mirrored"): ts = [ta, ta[:, ::-1], tb]; cap = (f"Pair {tag}: " if tag else "") + "left region as published, the same region mirrored, and the right region as published" + (f" ({p['note']})" if p.get("note") else "")
        f0 = f"{pk}/{s['id']}_{n}_pair.png"; cv2.imwrite(f0, side_by_side(ts)); imgs.append({"path": f0, "caption": cap, "color": True})
        byfig.setdefault(p["a"], []).append((p["abox"], COL[n % len(COL)], tag and tag + "1")); byfig.setdefault(p["b"], []).append((p["bbox"], COL[n % len(COL)], tag and tag + "2"))
    for n, (f, boxes) in enumerate(byfig.items()):
        f1 = f"{pk}/{s['id']}_ctx{n}.png"; cv2.imwrite(f1, context(out / "figs" / f, boxes, s.get("pad", 0.6)))
        imgs.append({"path": f1, "caption": "Where the regions sit in the published figure" + (" (same colour and letter = same pair)" if len(pairs) > 1 else ""), "color": True})
    imgs += [{"path": e["path"], "caption": e["caption"], "color": True} for e in s.get("extra", [])]
    head = f"{r['pmcid']}, {r['journal']} {r['year']}" + (f", doi:{r['doi']}" if r.get("doi") else "")
    items.append({"id": s["id"], "label": f"{head}. {s['what']}", "why": s["why"], "images": imgs})
json.dump(items, open(f"{pk}/items.json", "w")); print(len(items), "items")

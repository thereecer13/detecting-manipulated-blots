"""Larger look at chosen hits: both regions with wide context, plus the captions.

    python3 ctx.py OUTDIR N [N ...]     (N = hit number printed on the triage sheets)  ->  OUTDIR/view/ctx_N.jpg
"""
import json, sys
from pathlib import Path
import cv2
import numpy as np

out = Path(sys.argv[1]); want = {int(x) for x in sys.argv[2:]}


def crop(path, box, pad=1.0, side=900):
    im = cv2.imread(str(path)); x0, y0, x1, y1 = box; p = int(pad * max(x1 - x0, y1 - y0)) + 20
    X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(im.shape[1], x1 + p), min(im.shape[0], y1 + p)
    c = im[Y0:Y1, X0:X1].copy(); cv2.rectangle(c, (x0 - X0, y0 - Y0), (x1 - X0, y1 - Y0), (0, 0, 255), 2)
    s = side / max(c.shape[:2]); c = cv2.resize(c, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC if s > 1 else cv2.INTER_AREA)
    t = np.full((side, side, 3), 255, np.uint8); t[:c.shape[0], :c.shape[1]] = c
    return t


n = 0
for l in (out / "papers.jsonl").open():
    d = json.loads(l); caps = {f["file"]: f["caption"] for f in d["figs"]}
    for h in d["hits"]:
        if h.get("ncc", 1) < 0.5: continue
        if n in want:
            cv2.imwrite(str(out / "view" / f"ctx_{n}.jpg"), np.hstack([crop(out / "figs" / h["a"], h["abox"]), np.zeros((900, 10, 3), np.uint8), crop(out / "figs" / h["b"], h["bbox"])]), [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(f"== {n} {d['pmcid']} {d['journal']} {d['year']} | {d['title']}\n  A {h['a']} {h['abox']}\n    {caps[h['a']][:1500]}")
            if h["b"] != h["a"]: print(f"  B {h['b']} {h['bbox']}\n    {caps[h['b']][:1500]}")
        n += 1

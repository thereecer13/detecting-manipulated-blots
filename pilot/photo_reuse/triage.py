"""Tile every hit of a scan for a quick look: the two matched regions side by side, with context.

    python3 triage.py OUTDIR [per_sheet]     ->  OUTDIR/view/sheet_N.jpg, and a printed index
"""
import json, sys
from pathlib import Path
import os
import cv2
import numpy as np

# GREY=1 keeps only matches whose two regions contain bright, unsaturated pixels (mouse photographs,
# bright-field); it drops fluorescence panels, where single-channel and merged views match each other.
# SKIP=n ignores the first n papers of the scan (already reviewed).
GREY = os.environ.get("GREY") == "1"; SKIP = int(os.environ.get("SKIP", 0))


def grey(path, box):
    im = cv2.imread(str(path))
    if im is None: return False
    x0, y0, x1, y1 = box; hsv = cv2.cvtColor(im[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
    return hsv.size > 0 and float(((hsv[..., 1] < 40) & (hsv[..., 2] > 90)).mean()) >= 0.15

MINNCC = 0.5
out = Path(sys.argv[1]); per = int(sys.argv[2]) if len(sys.argv) > 2 else 8
(out / "view").mkdir(exist_ok=True)


def crop(path, box, pad=0.35, side=360):
    im = cv2.imread(str(path))
    if im is None: return np.full((side, side, 3), 128, np.uint8)
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; p = int(pad * max(w, h)) + 10
    X0, Y0, X1, Y1 = max(0, x0 - p), max(0, y0 - p), min(im.shape[1], x1 + p), min(im.shape[0], y1 + p)
    c = im[Y0:Y1, X0:X1].copy(); cv2.rectangle(c, (x0 - X0, y0 - Y0), (x1 - X0, y1 - Y0), (0, 0, 255), 2)
    s = side / max(c.shape[:2]); c = cv2.resize(c, (max(1, int(c.shape[1] * s)), max(1, int(c.shape[0] * s))))
    t = np.full((side, side, 3), 255, np.uint8); t[:c.shape[0], :c.shape[1]] = c
    return t


rows, idx = [], []
for ln, l in enumerate((out / "papers.jsonl").open()):
    if ln < SKIP: continue
    d = json.loads(l)
    for k, h in enumerate(d["hits"]):
        if h.get("ncc", 1) < MINNCC: continue
        # one figure stored twice (colour / print versions, or an extra copy named Figa, Figb ...)
        if h["a"] != h["b"] and abs(h["scale"] - 1) < 0.01 and h["abox"][:2] == h["bbox"][:2]: continue
        if "_OC." in h["a"] and "_PB." in h["b"]: continue
        if GREY and not (grey(out / "figs" / h["a"], h["abox"]) and grey(out / "figs" / h["b"], h["bbox"])): continue
        a, b = crop(out / "figs" / h["a"], h["abox"]), crop(out / "figs" / h["b"], h["bbox"])
        row = np.hstack([a, np.full((360, 8, 3), 0, np.uint8), b])
        head = np.full((24, row.shape[1], 3), 255, np.uint8)
        fa, fb = h["a"].split("_", 1)[1][-18:], h["b"].split("_", 1)[1][-18:]
        txt = f"{len(rows)} {d['pmcid']} {fa} | {fb} n{h['inliers']} c{h.get('ncc')} s{h['scale']} r{h['rotation']}{' MIR' if h['mirrored'] else ''}"
        cv2.putText(head, txt, (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        rows.append(np.vstack([head, row])); idx.append((len(rows) - 1, d["pmcid"], k))
for i in range(0, len(rows), per):
    cols = [np.vstack(rows[j:j + per // 2]) for j in (i, i + per // 2) if rows[j:j + per // 2]]
    H = max(c.shape[0] for c in cols)
    cols = [np.vstack([c, np.full((H - c.shape[0], c.shape[1], 3), 255, np.uint8)]) for c in cols]
    cv2.imwrite(str(out / "view" / f"sheet_{i // per}.jpg"), np.hstack(cols), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(len(rows), "hits on", (len(rows) + per - 1) // per, "sheets")

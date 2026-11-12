"""Find microscopy panels that are reused between different products.

Each figure is split into panels along white gutters (rows/columns that are almost entirely
near-white). Each panel is converted to gray, resized to a fixed width, and its central 70% is searched
in every panel of every other product with normalized cross-correlation at several scales (figures
use 2x2, 2x3 ... grids, so the same panel can appear at different sizes). Text labels sit at panel
corners, so the central crop mostly avoids them. Pairs above --min are reported, best first.

    python pilot/panel_dupes.py index.jsonl images_dir --out pairs.json [--min 0.9]

index.jsonl lines need "file" and "catalog" (pairs within one catalog are skipped).
"""
import argparse, itertools, json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

W = 128
SCALES = (0.8, 0.9, 1.0, 1.12, 1.25)


def runs(mask):
    out, start = [], None
    for i, v in enumerate(list(mask) + [True]):
        if not v and start is None: start = i
        if v and start is not None: out.append((start, i)); start = None
    return out


def split(rgb):
    """Panel boxes (x0, y0, x1, y1) between near-white gutters; panels smaller than 8% of a side are dropped."""
    white = (rgb.min(axis=2) >= 225)
    H, Wd = white.shape
    rows = runs(white.mean(1) > 0.9); cols = runs(white.mean(0) > 0.9)
    boxes = []
    for y0, y1 in rows:
        for x0, x1 in cols:
            if y1 - y0 < 0.08 * H or x1 - x0 < 0.08 * Wd: continue
            sub = white[y0:y1, x0:x1]
            if sub.mean() > 0.5: continue
            # inner columns within this row band (grids whose gutters do not span the whole figure)
            inner = runs(sub.mean(0) > 0.9)
            for a, b in inner:
                if b - a >= 0.08 * Wd: boxes.append((x0 + a, y0, x0 + b, y1))
    return boxes


def prep(gray):
    h, w = gray.shape
    g = cv2.resize(gray, (W, max(16, round(h * W / w))), interpolation=cv2.INTER_AREA).astype(np.float32)
    return g


def load(path):
    rgb = np.asarray(Image.open(path).convert("RGB"))
    out = []
    for (x0, y0, x1, y1) in split(rgb):
        p = rgb[y0:y1, x0:x1]
        g = cv2.cvtColor(p, cv2.COLOR_RGB2GRAY)
        if g.std() < 3: continue          # blank panel
        out.append({"box": (x0, y0, x1, y1), "g": prep(g)})
    return out


def match(a, b):
    """Best NCC of a's central 70% (at several scales) inside b."""
    best = -1.0
    for s in SCALES:
        aa = cv2.resize(a, (max(16, round(a.shape[1] * s)), max(16, round(a.shape[0] * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        h, w = aa.shape; t = aa[round(.15 * h):round(.85 * h), round(.15 * w):round(.85 * w)]
        if t.shape[0] > b.shape[0] or t.shape[1] > b.shape[1] or t.std() < 2: continue
        best = max(best, float(cv2.matchTemplate(b, t, cv2.TM_CCOEFF_NORMED).max()))
    return best


P = None
def _init(panels): global P; P = panels
def _pair(ij):
    i, j = ij
    return i, j, max(match(P[i]["g"], P[j]["g"]), match(P[j]["g"], P[i]["g"]))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("index", type=Path); ap.add_argument("images", type=Path)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--min", type=float, default=0.9); ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    recs = [json.loads(l) for l in a.index.read_text().splitlines()]
    panels = []
    for r in recs:
        try: ps = load(a.images / r["file"])
        except Exception: continue
        for k, p in enumerate(ps): panels.append({**p, "catalog": r["catalog"], "file": r["file"], "url": r.get("url"), "k": k})
    print(len(recs), "figures,", len(panels), "panels", flush=True)
    pairs = [(i, j) for i, j in itertools.combinations(range(len(panels)), 2) if panels[i]["catalog"] != panels[j]["catalog"]]
    with ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(panels,)) as ex:
        res = [r for r in ex.map(_pair, pairs, chunksize=200) if r[2] >= a.min]
    res.sort(key=lambda r: -r[2])
    out = [{"score": s, "a": {k: panels[i][k] for k in ("catalog", "file", "url", "box", "k")}, "b": {k: panels[j][k] for k in ("catalog", "file", "url", "box", "k")}} for i, j, s in res]
    a.out.write_text(json.dumps(out, indent=1))
    print(len(out), "cross-product panel pairs with score >=", a.min)
    for o in out[:30]: print(f"{o['score']:.3f} {o['a']['catalog']} p{o['a']['k']} ~ {o['b']['catalog']} p{o['b']['k']}")


if __name__ == "__main__":
    main()

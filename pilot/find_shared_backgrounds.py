"""Search for blot panels that share background noise across images (copied backgrounds), to find
reuse that Richardson's spreadsheet does not record.

Each image is split into blot panels (the same page/panel detection as views.blot_mask). Each panel
is resized to a fixed width, its noise residual (image minus Gaussian blur) is taken over the
background only (darkest 35% masked: bands, labels), normalized, and compared with every other
panel of similar aspect ratio by a dot product (correlation scaled by background overlap). Pairs
from the same known template letter are skipped; everything else above --min is reported.
Checked on Richardson's templates: copies of one template score >= 0.6 (median ~0.9), different
templates <= 0.25 (--validate).

Compared items:
  - every scraped vendor image (not in Richardson's list, so 'clean' as far as his data goes)
  - every Richardson image NOT flagged for a cross-image problem (painting etc.)
  - up to --per-template exemplars of each Richardson background pattern A-H

    python pilot/find_shared_backgrounds.py --richardson raw/rich_aug --scraped scraped --out shared_bg.json
"""
import argparse, csv, io, json, re, zipfile
from collections import defaultdict
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

W = 192
CROSS = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)


def panels(g):
    """Bounding boxes (x, y, w, h) of blot panels; the whole image if none is found."""
    h, w = g.shape
    white = (cv2.GaussianBlur(g, (3, 3), 0) >= 246).astype(np.uint8)
    n, lab = cv2.connectedComponents(white, 4)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    page = np.isin(lab, list(border)) & (white > 0)
    if page.mean() < 0.05:
        return [(0, 0, w, h)]
    rest = cv2.morphologyEx((~page).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(rest, 8)
    out = [tuple(int(v) for v in stats[i][:4]) for i in range(1, n)
           if stats[i][4] >= 0.015 * h * w and stats[i][2] >= 0.05 * w and stats[i][3] >= 0.05 * h]
    return out or [(0, 0, w, h)]


def fingerprint(crop, H):
    """Background grain of a panel as a unit vector. The panel is trimmed by 8% on each side, and the
    residual's row and column means are removed: edge ringing at the panel border, JPEG artifacts
    along flat edges and lane streaks are 1-D and identical across images with the same layout,
    while copied background grain is 2-D."""
    h, w = crop.shape; dy, dx = max(2, round(0.08 * h)), max(2, round(0.08 * w))
    crop = crop[dy:h - dy, dx:w - dx]
    if crop.shape[0] < 16 or crop.shape[1] < 16: return None
    g = cv2.resize(crop.astype(np.float32), (W, H), interpolation=cv2.INTER_AREA)
    r = g - cv2.GaussianBlur(g, (0, 0), 1.5)
    page = cv2.dilate((cv2.GaussianBlur(g, (3, 3), 0) >= 236).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    if (~page).sum() < 400: return None         # printed labels and ladders sit on white page: drop it and a margin
    m = ~page & (g > np.percentile(g[~page], 35))
    if m.sum() < 400: return None
    r = r - r.mean(1, keepdims=True); r = r - r.mean(0, keepdims=True)
    x = np.where(m, r - r[m].mean(), 0).astype(np.float32)
    if x[m].std() < MIN_GRAIN: return None      # flat, over-processed background: no grain to match
    return (x / np.linalg.norm(x)).ravel()


MIN_GRAIN = 0.8
BIN = 0.06
def bins_of(ar):
    b = np.log(ar) / BIN
    return sorted({int(np.floor(b)), int(np.round(b))})   # own bin and the nearer neighbour


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--richardson", type=Path, required=True)
    ap.add_argument("--scraped", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--per-template", type=int, default=40)
    ap.add_argument("--min", type=float, default=0.25)
    ap.add_argument("--validate", action="store_true", help="templates only; report same-template pairs (known copies) and cross-template pairs")
    a = ap.parse_args()
    sheet = next(a.richardson.glob("*_catch_all_spreadsheet.csv")); z = zipfile.ZipFile(next(a.richardson.glob("*_original_images.zip")))
    names = {Path(n).name: n for n in z.namelist()}
    items = []          # (key, source, info, loader)
    tcount = defaultdict(int)
    for r in csv.DictReader(open(sheet, encoding="utf-8")):
        f = r["original_image_filename"]
        if f not in names: continue
        m = re.search(r"pattern ([A-Z])", r["summary"])
        if m:
            if tcount[m.group(1)] >= a.per_template: continue
            tcount[m.group(1)] += 1; src = "template_" + m.group(1)
        elif a.validate or CROSS.search(r["summary"]):
            continue                                   # already recorded as a cross-image problem
        else:
            src = "richardson_within"
        items.append((f"R{r['image_index']}", src, {"catalog": r["catalog_number"], "vendor": r["vendor"], "summary": r["summary"], "file": f},
                      lambda n=names[f]: Image.open(io.BytesIO(z.read(n)))))
    for l in ([] if a.validate else (a.scraped / "screened.jsonl").read_text().splitlines()):
        d = json.loads(l)
        items.append((f"S{d['catalog']}", "scraped", {"catalog": d["catalog"], "vendor": d["vendor"], "file": d["file"], "kept": d["keep"], "image_url": d["image_url"]},
                      lambda p=a.scraped / "images" / d["file"]: Image.open(p)))
    print(f"{len(items)} images:", dict(sorted(defaultdict(int, {s: sum(1 for i in items if i[1] == s) for s in {i[1] for i in items}}).items())))
    by_bin = defaultdict(list); meta = []
    for k, (key, src, info, load) in enumerate(items):
        try: g = np.asarray(load().convert("L"))
        except Exception: continue
        for j, (x, y, w, h) in enumerate(panels(g)):
            if w < 60 or h < 30: continue
            pid = len(meta); meta.append({"item": key, "src": src, "panel": j, "box": [x, y, w, h], **info})
            for b in bins_of(h / w):
                fp = fingerprint(g[y:y + h, x:x + w], max(16, round(W * np.exp(b * BIN))))
                if fp is not None: by_bin[b].append((pid, fp))
        if k % 500 == 0: print(f"  {k}/{len(items)}", flush=True)
    best = {}
    for b, lst in by_bin.items():
        if len(lst) < 2: continue
        ids = np.array([p for p, _ in lst]); X = np.stack([f for _, f in lst])
        S = X @ X.T
        ii, jj = np.where(np.triu(S, 1) >= a.min)
        for i, j in zip(ii, jj):
            p, q = sorted((int(ids[i]), int(ids[j])))
            A, B = meta[p], meta[q]
            if A["item"] == B["item"] and A["panel"] == B["panel"]: continue
            if A["src"] == B["src"] and A["src"].startswith("template_") and not a.validate: continue   # same known template
            best[(p, q)] = max(best.get((p, q), 0), float(S[i, j]))
    pairs = sorted(({"score": round(s, 3), "a": meta[p], "b": meta[q]} for (p, q), s in best.items()), key=lambda d: -d["score"])
    a.out.write_text(json.dumps(pairs, indent=1))
    if a.validate:
        tm = [m for m in meta if m["src"].startswith("template_")]
        for L in sorted({m["src"] for m in tm}):
            items_L = {m["item"] for m in tm if m["src"] == L}
            hit = {x for d in pairs if d["a"]["src"] == d["b"]["src"] == L and d["a"]["item"] != d["b"]["item"] for x in (d["a"]["item"], d["b"]["item"])}
            print(f"{L}: {len(hit)}/{len(items_L)} images matched to another image of the same template")
        print("cross-template pairs:", sum(d["a"]["src"] != d["b"]["src"] for d in pairs))
    print(f"{len(meta)} panels, {len(pairs)} pairs >= {a.min}")
    for d in pairs[:40]:
        print(f"{d['score']:.2f}  {d['a']['src']:17s} {d['a']['item']:14s} {d['a']['catalog']:16s} | {d['b']['src']:17s} {d['b']['item']:14s} {d['b']['catalog']}")


if __name__ == "__main__":
    main()

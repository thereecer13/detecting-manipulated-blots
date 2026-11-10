"""Find blots whose background matches one of Richardson's background templates (patterns A-H).

Each figure is reduced to its largest blot panel (page and printed labels excluded), trimmed by 5%,
scaled to a common width and turned into a background-noise map: image minus a light blur, row and
column means removed (edge ringing and lane streaks are shared by layout), bands (darkest 35%) and
page pixels set to zero. The central 80% of one map is searched for in the other (zero-padded by
15% each side) with normalized cross-correlation over all shifts and three scales, in both
directions; the score is the best correlation. A different crop or a small rescale of the same
background still matches.

Use it as a candidate generator; every candidate is checked by eye. Validation (held-out Richardson
Thermo template images vs 37 user-verified clean blots, 63 fresh scraped blots and 100 Richardson
non-template images): at score >= 0.4, recall A 14/25, B 16/25, C 19/25, D 20/25; 4 of 200
negatives pass, all heavily painted figures whose few surviving grainy patches match by chance.
Masking flat areas (--flat, --min-valid) removes those but collapses pattern B recall (faint grain),
so it is off by default.

    python pilot/template_match.py validate --richardson raw/rich_aug --clean <dir with clean images> ...
    python pilot/template_match.py scan --richardson raw/rich_aug --scraped scraped_tmpl --out matches.json
"""
import argparse, csv, io, json, re, sys, zipfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from find_shared_backgrounds import panels
Image.MAX_IMAGE_PIXELS = None

W = 200
SCALES = (0.9, 1.0, 1.1)
MIN_VALID = 0.0    # share of the panel that must be usable background (0 = off)
FLAT = -1.0        # local residual RMS below which background counts as flat and is masked (-1 = off)


def noise_map(img):
    g = np.asarray(img.convert("L"))
    x, y, w, h = max(panels(g), key=lambda b: b[2] * b[3])
    dx, dy = round(0.05 * w), round(0.05 * h)
    p = g[y + dy:y + h - dy, x + dx:x + w - dx].astype(np.float32)
    if p.shape[0] < 20 or p.shape[1] < 20: return None
    H = max(20, round(p.shape[0] * W / p.shape[1]))
    p = cv2.resize(p, (W, H), interpolation=cv2.INTER_AREA)
    r = p - cv2.GaussianBlur(p, (0, 0), 1.2)
    r = r - r.mean(1, keepdims=True); r = r - r.mean(0, keepdims=True)
    page = cv2.dilate((p >= 236).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    if (~page).sum() < 400: return None
    m = ~page & (p > np.percentile(p[~page], 35))
    raw = p - cv2.GaussianBlur(p, (0, 0), 1.2)
    m &= np.sqrt(cv2.blur(raw * raw, (5, 5))) > FLAT     # drop perfectly flat (painted or clipped) areas
    if m.sum() < 400 or r[m].std() < 0.3: return None
    if m.mean() < MIN_VALID: return None        # mostly flat or page: too little background to compare
    r = np.where(m, (r - r[m].mean()) / r[m].std(), 0).astype(np.float32)
    return r


def _one_way(a, b):
    h, w = a.shape; ty, tx = round(0.1 * h), round(0.1 * w)
    t = a[ty:h - ty, tx:w - tx]
    if not t.any(): return 0.0
    best = 0.0
    for s in SCALES:
        bb = cv2.resize(b, (max(8, round(b.shape[1] * s)), max(8, round(b.shape[0] * s))), interpolation=cv2.INTER_LINEAR)
        py, px = round(0.15 * bb.shape[0]), round(0.15 * bb.shape[1])
        bb = cv2.copyMakeBorder(bb, py, py, px, px, cv2.BORDER_CONSTANT, value=0)
        if bb.shape[0] < t.shape[0] or bb.shape[1] < t.shape[1]: continue
        best = max(best, float(cv2.matchTemplate(bb, t, cv2.TM_CCORR_NORMED).max()))
    return best


def match(a, b):
    return max(_one_way(a, b), _one_way(b, a))


def richardson(rich_dir):
    sheet = next(Path(rich_dir).glob("*_catch_all_spreadsheet.csv"))
    z = zipfile.ZipFile(next(Path(rich_dir).glob("*_original_images.zip")))
    names = {Path(n).name: n for n in z.namelist()}
    rows = [r for r in csv.DictReader(open(sheet, encoding="utf-8")) if r["original_image_filename"] in names]
    return rows, (lambda r: Image.open(io.BytesIO(z.read(names[r["original_image_filename"]]))))


def template_rows(rows, vendor_host="thermofisher.com"):
    out = {}
    for r in rows:
        m = re.search(r"pattern ([A-Z])", r["summary"])
        if m and vendor_host in r["product_link"]: out.setdefault(m.group(1), []).append(r)
    return out


def bank(rows_by_pattern, load, n, rng):
    ex, held = {}, {}
    for L, rr in rows_by_pattern.items():
        rr = rr[:]; rng.shuffle(rr)
        maps = []
        for r in rr:
            if len(maps) >= n: break
            try: m = noise_map(load(r))
            except Exception: m = None
            if m is not None: maps.append((r["catalog_number"], m))
        ex[L] = maps; held[L] = [r for r in rr if r["catalog_number"] not in {c for c, _ in maps}]
    return ex, held


def best_match(m, ex):
    best = (0.0, None, None)
    for L, maps in ex.items():
        for cat, e in maps:
            s = match(m, e)
            if s > best[0]: best = (s, L, cat)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["validate", "scan"])
    ap.add_argument("--richardson", type=Path, required=True)
    ap.add_argument("--clean", nargs="*", type=Path, default=[], help="validate: clean image files (negatives)")
    ap.add_argument("--scraped", type=Path, help="scan: folder with scraped.jsonl and images/")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--per-pattern", type=int, default=20, help="exemplars per pattern")
    ap.add_argument("--held", type=int, default=25, help="validate: held-out template images per pattern")
    ap.add_argument("--min-valid", type=float, default=MIN_VALID)
    ap.add_argument("--flat", type=float, default=FLAT)
    a = ap.parse_args()
    globals().update(MIN_VALID=a.min_valid, FLAT=a.flat)
    rng = __import__("random").Random(7)
    rows, load = richardson(a.richardson)
    ex, held = bank(template_rows(rows), load, a.per_pattern, rng)
    print("exemplars:", {L: len(v) for L, v in ex.items()}, flush=True)
    if a.mode == "validate":
        res = []
        for L, rr in held.items():
            k = 0
            for r in rr:
                if k >= a.held: break
                try: m = noise_map(load(r))
                except Exception: m = None
                if m is None: res.append({"kind": "template", "pattern": L, "score": None}); k += 1; continue
                s, BL, cat = best_match(m, ex); k += 1
                res.append({"kind": "template", "pattern": L, "score": s, "best_pattern": BL, "catalog": r["catalog_number"]})
        for f in a.clean:
            try: m = noise_map(Image.open(f))
            except Exception: m = None
            if m is None: res.append({"kind": "clean", "score": None, "file": f.name}); continue
            s, BL, cat = best_match(m, ex)
            res.append({"kind": "clean", "score": s, "best_pattern": BL, "file": f.name})
        if a.out: a.out.write_text(json.dumps(res, indent=1))
        T = [r for r in res if r["kind"] == "template"]; C = [r for r in res if r["kind"] == "clean"]
        print(f"templates: {len(T)}, unscorable {sum(r['score'] is None for r in T)}; clean: {len(C)}, unscorable {sum(r['score'] is None for r in C)}")
        cs = sorted([r["score"] for r in C if r["score"] is not None], reverse=True)
        print("clean top scores:", [round(x, 3) for x in cs[:8]])
        for thr in (0.2, 0.25, 0.3, 0.35, 0.4, 0.5):
            rec = {L: f"{sum(1 for r in T if r['pattern'] == L and r['score'] and r['score'] >= thr and r['best_pattern'] == L)}/{sum(1 for r in T if r['pattern'] == L)}" for L in ex}
            print(f"thr {thr}: template recall (right pattern) {rec} | clean above {sum(x >= thr for x in cs)}/{len(C)}")
    else:
        recs = [json.loads(l) for l in (a.scraped / "scraped.jsonl").read_text().splitlines()]
        out = []
        for i, rec in enumerate(recs):
            try: m = noise_map(Image.open(a.scraped / "images" / rec["file"]))
            except Exception: m = None
            s, L, cat = best_match(m, ex) if m is not None else (None, None, None)
            out.append({**rec, "score": s, "pattern": L, "exemplar": cat})
            if i % 50 == 0: print(f"  {i}/{len(recs)}", flush=True)
        a.out.write_text(json.dumps(out, indent=1))
        sc = sorted([o for o in out if o["score"] is not None], key=lambda o: -o["score"])
        print(f"{len(out)} images, unscorable {sum(o['score'] is None for o in out)}")
        for o in sc[:25]: print(f"{o['score']:.3f} {o['pattern']} {o['catalog']} ~ {o['exemplar']}")


if __name__ == "__main__":
    main()

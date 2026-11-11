"""Template detector v2: does a figure's background grain match one of Richardson's template groups?

Why v2: v1 (template_match.py) correlated whole panels, and Thermo reuses the same figure frame (box,
ladder, lane numbers, arrow position) across many products, so frame lines produced high scores for
blots whose background grain does not match at all (pilot: 0 of 31 candidates were real).

How v2 works:
1. Shape gate: template members share a figure frame, so a candidate is compared only with template
   groups whose figure aspect ratio (height/width) is within 3% of its own.
2. Alignment: the candidate is shrunk (or enlarged) to the exemplar's exact pixel size, +-2 px in
   width, and shifted by whole pixels (+-4) at that resolution; fine noise only correlates at exact
   pixel alignment.
3. Score: inside the blot panels only (page, printed labels and bands masked; bands are pixels much
   darker than their surroundings), the noise residuals are compared window by window (windows of
   ~1/25 of the figure width). `share` = fraction of valid windows whose correlation exceeds 0.5,
   `median` = median window correlation. A true template pair has most windows matching (reference
   pattern B pair: 82%); a shared frame alone gives a few percent.

    python pilot/template_scan2.py validate --richardson raw/rich_aug --negatives <image files> --out val.json
    python pilot/template_scan2.py scan --richardson raw/rich_aug --scraped scraped_tmpl --out scan.json [--jobs 4]
"""
import argparse, json, random, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
import template_match as tm
from views import blot_mask
Image.MAX_IMAGE_PIXELS = None

PATTERNS = ("A", "B")          # Thermo polyclonal templates; C/D/E-H can be added the same way
PER_GROUP = 4                  # exemplars per (pattern, aspect) group
ASPECT_TOL = 0.03
LOCAL = 0.5


def prep(g):
    """Noise residual and valid mask (blot panels only, no page, no labels, no bands)."""
    g = g.astype(np.float32)
    r = g - cv2.GaussianBlur(g, (0, 0), 1.2)
    page = cv2.dilate((g >= 236).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    k = max(15, (min(g.shape) // 8) | 1); k = min(k, 255) if min(k, 255) % 2 else min(k, 255) - 1
    local = cv2.medianBlur(np.clip(g, 0, 255).astype(np.uint8), k).astype(np.float32)
    band = cv2.dilate((g < local - 25).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    v = ~page & ~band & blot_mask(np.clip(g, 0, 255).astype(np.uint8))
    return np.where(v, r, 0).astype(np.float32), v


def resize_to(g, w, h):
    interp = cv2.INTER_AREA if w < g.shape[1] else cv2.INTER_LINEAR
    return cv2.resize(g.astype(np.float32), (w, h), interpolation=interp)


def compare(gc, ex):
    """gc: candidate gray image; ex: exemplar dict (residual, mask, shape). Best alignment, then window
    statistics. Returns dict(share, median, corr, w, dx, dy)."""
    re_, ve = ex["r"], ex["v"]; H, W = ve.shape
    best = None
    for wt in range(W - 2, W + 3):
        ht = round(gc.shape[0] * wt / gc.shape[1])
        if abs(ht - H) > 6: continue
        rc, vc = prep(resize_to(gc, wt, ht))
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                # exemplar pixel (y, x) <-> candidate pixel (y + dy, x + dx), over the common area
                y0, y1 = max(0, -dy), min(H, ht - dy); x0, x1 = max(0, -dx), min(W, wt - dx)
                if y1 - y0 < 40 or x1 - x0 < 40: continue
                a = re_[y0:y1, x0:x1]; b = rc[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                m = ve[y0:y1, x0:x1] & vc[y0 + dy:y1 + dy, x0 + dx:x1 + dx]
                if m.sum() < 500: continue
                x, y = a[m], b[m]
                if x.std() < 1e-6 or y.std() < 1e-6: continue
                c = float(np.corrcoef(x, y)[0, 1])
                if best is None or c > best[0]: best = (c, wt, dx, dy, a, b, m)
    if best is None: return {"share": 0.0, "median": 0.0, "corr": -1.0}
    c, wt, dx, dy, a, b, m = best
    win = max(7, round(W / 25)) | 1; k = (win, win)
    a, b = np.where(m, a, 0), np.where(m, b, 0)
    num = cv2.blur(a * b, k); den = np.sqrt(cv2.blur(a * a, k) * cv2.blur(b * b, k))
    cover = cv2.blur(m.astype(np.float32), k)
    ok = (den > 1e-6) & (cover > 0.5)
    lc = np.where(ok, num / np.maximum(den, 1e-6), 0)
    vals = lc[ok & m]
    if vals.size == 0: return {"share": 0.0, "median": 0.0, "corr": c}
    return {"share": float((vals > LOCAL).mean()), "median": float(np.median(vals)), "corr": c, "w": wt, "dx": dx, "dy": dy}


def exemplar_groups(rows, load, rng, per_group=PER_GROUP, exclude=()):
    tr = tm.template_rows(rows); groups = {}
    for L in PATTERNS:
        rr = [r for r in tr.get(L, []) if r["catalog_number"] not in exclude]; rng.shuffle(rr)
        for r in rr:
            try: g = np.asarray(load(r).convert("L")).astype(np.float32)
            except Exception: continue
            asp = round(g.shape[0] / g.shape[1], 2)
            key = (L, asp)
            if len(groups.setdefault(key, [])) >= per_group: continue
            res, v = prep(g)
            if v.mean() < 0.15: continue
            groups[key].append({"catalog": r["catalog_number"], "r": res, "v": v})
    return {k: v for k, v in groups.items() if v}


def score_image(g, groups):
    asp = g.shape[0] / g.shape[1]; best = {"share": 0.0, "median": 0.0, "corr": -1.0, "pattern": None, "exemplar": None}
    for (L, ga), exs in groups.items():
        if abs(asp / ga - 1) > ASPECT_TOL: continue
        for ex in exs:
            s = compare(g, ex)
            if s["share"] > best["share"] or (best["pattern"] is None and s["corr"] > best["corr"]):
                best = {**s, "pattern": L, "exemplar": ex["catalog"]}
    return best


_G = None
def _init(rich, seed, exclude):
    global _G
    rows, load = tm.richardson(rich)
    _G = exemplar_groups(rows, load, random.Random(seed), exclude=set(exclude))


def _work(path):
    try: g = np.asarray(Image.open(path).convert("L")).astype(np.float32)
    except Exception as e: return {"path": str(path), "error": str(e)[:80]}
    return {"path": str(path), **score_image(g, _G)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["validate", "scan"])
    ap.add_argument("--richardson", type=Path, required=True)
    ap.add_argument("--negatives", nargs="*", type=Path, default=[])
    ap.add_argument("--held", type=int, default=30, help="validate: held-out members per pattern")
    ap.add_argument("--scraped", type=Path); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--jobs", type=int, default=4); ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    rows, load = tm.richardson(a.richardson)
    tr = tm.template_rows(rows); rng = random.Random(a.seed)
    paths, kinds = [], []
    if a.mode == "validate":
        # held-out members (excluded from exemplars), simulated as the site's 650-px JPEG rendition
        G = exemplar_groups(rows, load, random.Random(a.seed))
        used = {e["catalog"] for exs in G.values() for e in exs}
        hold = Path(a.out.parent / "heldout_members"); hold.mkdir(exist_ok=True)
        for L in PATTERNS:
            rr = [r for r in tr[L] if r["catalog_number"] not in used]; rng.shuffle(rr)
            for r in rr[:a.held]:
                im = load(r).convert("L"); w, h = im.size
                im = im.resize((650, round(h * 650 / w)), Image.LANCZOS)
                p = hold / f"{L}_{r['catalog_number']}.jpg"; im.save(p, "JPEG", quality=85)
                paths.append(p); kinds.append(("member", L))
        for p in a.negatives: paths.append(p); kinds.append(("negative", None))
        exclude = sorted({r["catalog_number"] for L in PATTERNS for r in tr[L]} - used)   # keep exemplar set identical
        init = (str(a.richardson), a.seed, [])
    else:
        recs = [json.loads(l) for l in (a.scraped / "scraped.jsonl").read_text().splitlines()]
        paths = [a.scraped / "images" / r["file"] for r in recs]; kinds = [("scraped", None)] * len(paths)
        init = (str(a.richardson), a.seed, [])
    with ProcessPoolExecutor(a.jobs, initializer=_init, initargs=init) as ex:
        res = list(ex.map(_work, paths, chunksize=4))
    for r, k in zip(res, kinds): r["kind"], r["true_pattern"] = k
    if a.mode == "scan":
        for r, rec in zip(res, recs): r.update({"catalog": rec["catalog"], "image_url": rec["image_url"]})
    a.out.write_text(json.dumps(res, indent=1))
    gated = [r for r in res if r.get("pattern")]
    print(f"{len(res)} images, {len(gated)} passed the shape gate")
    if a.mode == "validate":
        for thr in (0.1, 0.2, 0.3, 0.4, 0.5):
            mem = [r for r in res if r["kind"] == "member"]; neg = [r for r in res if r["kind"] == "negative"]
            rec = {L: f"{sum(1 for r in mem if r['true_pattern'] == L and r.get('pattern') == L and r['share'] >= thr)}/{sum(1 for r in mem if r['true_pattern'] == L)}" for L in PATTERNS}
            print(f"share >= {thr}: recall {rec} | negatives above {sum(1 for r in neg if r.get('share', 0) >= thr)}/{len(neg)} (gated {sum(1 for r in neg if r.get('pattern'))})")
        print("negatives top shares:", sorted([round(r.get('share', 0), 2) for r in res if r['kind'] == 'negative'], reverse=True)[:10])
    else:
        for r in sorted(gated, key=lambda r: -r["share"])[:25]:
            print(f"{r['share']:.2f} median {r['median']:.2f} {r['pattern']} {r['catalog']} ~ {r['exemplar']}")


if __name__ == "__main__":
    main()

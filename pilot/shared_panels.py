"""Find microscopy panels shared between different antibody products, including near-black panels.

Some reused "no primary antibody" control panels are so dark that they look like black boxes; when
their levels are stretched, cell structure appears. So every panel is level-stretched on its own before
comparison:
  * panels: figures are split along white gutters (panel_dupes.split)
  * stretch: brightest channel per pixel; text labels (near-white or saturated pixels, dilated) are
    ignored when choosing the white point (99.5th percentile of the rest); gamma 0.5
  * fingerprint: central crop of the stretched panel, 32x32, zero-mean / unit-norm. Index crops cover
    60% of the panel; queries use 50-75% crops, so a panel shown at 0.8-1.25x relative size still
    matches. Nearest neighbours by cosine similarity (matrix product, in chunks).
  * verification: multi-scale normalized cross-correlation of the stretched panels (panel_dupes.match)
Pairs within one catalog number are skipped. Identical image URLs on several product pages are
reported separately (same file reused as a whole).

    python pilot/shared_panels.py index.jsonl [index2.jsonl ...] --images DIR [DIR2 ...] --out pairs.json
    python pilot/shared_panels.py --show pairs.json --images DIR ... --out-dir review/
"""
import argparse, json, re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).parent))
from panel_dupes import split, SCALES


def match(a, b, min_std=4.0):
    """Best NCC of a's central 70% (at several scales) inside b. Unlike panel_dupes.match, windows of b
    that are nearly flat are ignored: OpenCV's normalized correlation divides by the window's spread and
    returns ~1.0 on flat (e.g. clipped black) windows, which stretched dark panels have plenty of."""
    best = -1.0
    for s in SCALES:
        aa = cv2.resize(a, (max(16, round(a.shape[1] * s)), max(16, round(a.shape[0] * s))), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
        h, w = aa.shape; t = aa[round(.15 * h):round(.85 * h), round(.15 * w):round(.85 * w)]
        th, tw = t.shape
        if th > b.shape[0] or tw > b.shape[1] or t.std() < min_std: continue
        r = cv2.matchTemplate(b, t, cv2.TM_CCOEFF_NORMED)
        mu = cv2.boxFilter(b, -1, (tw, th), normalize=True, anchor=(0, 0), borderType=cv2.BORDER_CONSTANT)
        sq = cv2.boxFilter(b * b, -1, (tw, th), normalize=True, anchor=(0, 0), borderType=cv2.BORDER_CONSTANT)
        sd = np.sqrt(np.maximum(sq - mu * mu, 0))[:r.shape[0], :r.shape[1]]
        r = np.where((sd >= min_std) & np.isfinite(r), np.minimum(r, 1.0), -1)
        best = max(best, float(r.max()))
    return best

D = 32
INDEX_CROP = 0.6
QUERY_CROPS = (0.5, 0.55, 0.6, 0.67, 0.75)
KNN = 8
CAND = 0.6          # fingerprint cosine needed to verify a pair
VERIFY = 0.8        # NCC of the panels; pairs >= 0.85 are reported as matches, 0.8-0.85 as "review"
WV = 160            # width of stretched panels kept for verification
DETAIL = 0.55       # fine-detail NCC needed when both panels are bright
HUB_DEG = 4         # a dark panel matching this many others is a generic look-alike hub


# Synthetic test (pilot/controls/README.md): 106/148 darkened copies (peak gray ~6-25) found at >= 0.8,
# 86/148 at >= 0.85; the 5 known shared-control groups are all found.
def stretch(p):
    """Level-stretch one RGB panel (uint8) -> float32 gray in [0, 1] and a text mask."""
    f = p.astype(np.float32); g = f.max(2)
    txt = (f.min(2) > 150) | (g > 245)
    txt = cv2.dilate(txt.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    rest = g[~txt] if (~txt).sum() > 100 else g.ravel()
    lo, hi = np.percentile(rest, 1), np.percentile(rest, 99.5)
    s = np.clip((g - lo) / max(hi - lo, 1.0), 0, 1) ** 0.5
    s[txt] = np.median(s[~txt]) if (~txt).any() else 0
    return s.astype(np.float32), float(hi), txt


def fp(s, c):
    h, w = s.shape; t = s[round((1 - c) / 2 * h):round((1 + c) / 2 * h), round((1 - c) / 2 * w):round((1 + c) / 2 * w)]
    v = cv2.resize(cv2.GaussianBlur(t, (0, 0), max(t.shape) / D / 2), (D, D), interpolation=cv2.INTER_AREA).ravel()
    v = v - v.mean(); n = np.linalg.norm(v)
    return (v / n).astype(np.float32) if n > 1e-3 else None


def panels_of(job):
    rec, path = job
    try: rgb = np.asarray(Image.open(path).convert("RGB"))
    except Exception: return []
    out = []
    for k, (x0, y0, x1, y1) in enumerate(split(rgb)):
        p = rgb[y0:y1, x0:x1]
        if min(p.shape[:2]) < 40: continue
        s, hi, txt = stretch(p)
        if hi < 2 or s[~txt].std() < 0.05: continue          # truly empty even after stretching
        idx = fp(s, INDEX_CROP); qs = [fp(s, c) for c in QUERY_CROPS]
        if idx is None or any(q is None for q in qs): continue
        h, w = s.shape
        out.append({"catalog": rec["catalog"], "file": rec["file"], "url": rec.get("url"), "k": k, "box": [x0, y0, x1, y1],
                    "dark": hi < 60, "white": hi, "idx": idx, "q": np.stack(qs),
                    "v": cv2.resize(s, (WV, max(16, round(h * WV / w))), interpolation=cv2.INTER_AREA) * 255,
                    "g": cv2.resize(p.astype(np.float32).max(2), (WV, max(16, round(h * WV / w))), interpolation=cv2.INTER_AREA)})
    return out


def target(desc):
    m = re.search(r"analysis of (.+?)(?: was| in | using|\(|\.|,)", desc or "")
    return m.group(1).strip() if m else "?"


def _verify(args):
    """Best NCC of the plain panels (bright panels; stretching amplifies JPEG noise) or of the stretched
    panels (dark panels, where the plain ones are almost flat)."""
    (va, ga, da), (vb, gb, db) = args
    plain = max(match(ga, gb), match(gb, ga)) if ga.std() > 3 and gb.std() > 3 else -1
    if da or db:   # a dark panel has only a few gray levels: smooth away the quantization / JPEG blocks
        sa, sb = cv2.GaussianBlur(va, (0, 0), 1.5), cv2.GaussianBlur(vb, (0, 0), 1.5)
        return max(plain, match(sa, sb), match(sb, sa)), None
    # bright panels: the fine detail must match too. Panels with one or a few cells on black look alike
    # at low resolution (score > 0.9) but their fine texture does not (detail <= 0.35; true copies >= 0.7)
    ha, hb = va - cv2.GaussianBlur(va, (0, 0), 1.5), vb - cv2.GaussianBlur(vb, (0, 0), 1.5)
    return max(plain, match(va, vb), match(vb, va)), max(match(ha, hb, 1.0), match(hb, ha, 1.0))


def run(recs, roots, out, jobs):
    def path(r):
        for d in roots:
            if (d / r["file"]).exists(): return d / r["file"]
        return None
    # identical files reused on several product pages
    by_url = defaultdict(set)
    for r in recs: by_url[r.get("url")].add(r["catalog"])
    same_file = [{"url": u, "catalogs": sorted(c)} for u, c in by_url.items() if u and len(c) > 1]
    seen, uniq = set(), []
    for r in recs:
        if r["file"] in seen or path(r) is None: continue
        seen.add(r["file"]); uniq.append(r)
    with ProcessPoolExecutor(jobs) as ex: P = [p for ps in ex.map(panels_of, [(r, path(r)) for r in uniq], chunksize=8) for p in ps]
    print(f"{len(uniq)} figures, {len(P)} panels ({sum(p['dark'] for p in P)} dark)", flush=True)
    I = np.stack([p["idx"] for p in P]); cats = np.array([p["catalog"] for p in P])
    cand = {}
    for c in range(len(QUERY_CROPS)):
        Q = np.stack([p["q"][c] for p in P])
        for s in range(0, len(P), 2048):
            S = Q[s:s + 2048] @ I.T
            for i in range(S.shape[0]):
                row = S[i]; row[cats == cats[s + i]] = -1
                top = np.argpartition(-row, KNN)[:KNN] if len(row) > KNN else np.arange(len(row))
                for j in top:
                    if row[j] >= CAND:
                        key = (min(s + i, int(j)), max(s + i, int(j))); cand[key] = max(cand.get(key, -1), float(row[j]))
    print(f"{len(cand)} candidate pairs", flush=True)
    keys = list(cand)
    with ProcessPoolExecutor(jobs) as ex: sc = list(ex.map(_verify, [((P[i]["v"], P[i]["g"], P[i]["dark"]), (P[j]["v"], P[j]["g"], P[j]["dark"])) for i, j in keys], chunksize=64))
    tgt = {r["file"]: target(r.get("description")) for r in recs}
    pairs = []
    for (i, j), (v, det) in zip(keys, sc):
        if v < VERIFY or (det is not None and det < DETAIL): continue
        a, b = P[i], P[j]
        pairs.append({"score": round(v, 3), "fingerprint": round(cand[(i, j)], 3), "dark": a["dark"] or b["dark"], "detail": None if det is None else round(det, 3),
                      "tier": "dark: check by eye" if det is None else ("match" if v >= 0.85 else "review"),
                      "a": {k: a[k] for k in ("catalog", "file", "url", "k", "box")} | {"target": tgt[a["file"]], "white": round(a["white"])},
                      "b": {k: b[k] for k in ("catalog", "file", "url", "k", "box")} | {"target": tgt[b["file"]], "white": round(b["white"])}})
    # dark "hub" panels (lone cells, blobs, empty noise) loosely match many other dark panels; tag their
    # pairs instead of listing each one (the hub panels themselves are listed so a dark control reused
    # on many products is still seen)
    from collections import Counter
    deg = Counter((p[s]["file"], p[s]["k"]) for p in pairs if p["dark"] for s in ("a", "b"))
    hubs = {k for k, v in deg.items() if v >= HUB_DEG}
    for p in pairs:
        if p["dark"] and ((p["a"]["file"], p["a"]["k"]) in hubs or (p["b"]["file"], p["b"]["k"]) in hubs): p["tier"] = "dark: generic hub"
    pairs.sort(key=lambda p: -p["score"])
    out.write_text(json.dumps({"pairs": pairs, "same_file": same_file, "dark_hubs": [{"file": f, "k": k, "matches": deg[(f, k)]} for f, k in hubs]}, indent=1))
    print(f"{len(pairs)} verified cross-product panel pairs ({sum(p['dark'] for p in pairs)} involve a dark panel); "
          f"{len(same_file)} image files listed on several products", flush=True)
    for p in pairs[:40]:
        print(p["score"], p["fingerprint"], "DARK" if p["dark"] else "", p["a"]["catalog"], p["a"]["target"][:25], "~", p["b"]["catalog"], p["b"]["target"][:25])


def show(pairs_file, roots, out_dir, n=200):
    out_dir.mkdir(parents=True, exist_ok=True); data = json.loads(pairs_file.read_text())
    def path(f):
        for d in roots:
            if (d / f).exists(): return d / f
    for k, p in enumerate(data["pairs"][:n]):
        row = []
        for s in ("a", "b"):
            rgb = np.asarray(Image.open(path(p[s]["file"])).convert("RGB")); x0, y0, x1, y1 = p[s]["box"]
            pan = rgb[y0:y1, x0:x1]; st = (stretch(pan)[0] * 255).astype(np.uint8)
            for im in (pan, np.repeat(st[..., None], 3, 2)):
                row.append(np.asarray(Image.fromarray(im).resize((260, round(260 * im.shape[0] / im.shape[1])))))
        h = max(r.shape[0] for r in row)
        can = np.full((h, 4 * 265, 3), 255, np.uint8)
        for i, r in enumerate(row): can[:r.shape[0], i * 265:i * 265 + 260] = r
        Image.fromarray(can).save(out_dir / f"{k:03d}_{p['a']['catalog']}_{p['b']['catalog']}.png")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("index", nargs="*", type=Path)
    ap.add_argument("--images", nargs="+", type=Path, required=True); ap.add_argument("--out", type=Path)
    ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--show", type=Path); ap.add_argument("--out-dir", type=Path)
    a = ap.parse_args()
    if a.show: return show(a.show, a.images, a.out_dir)
    recs = [json.loads(l) for f in a.index for l in f.read_text().splitlines() if l.strip()]
    run(recs, a.images, a.out, a.jobs)


if __name__ == "__main__":
    main()

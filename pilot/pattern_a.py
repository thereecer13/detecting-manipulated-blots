"""Pattern A detector: single-lane Thermo blots that share Richardson pattern-A's lane background.

Why the template detector missed pattern A: it took exemplars from the figures in Richardson's archive,
which are cropped differently from one another. On Thermo's current product images, pattern-A
figures use one fixed layout (650 x 650 px, one lane boxed at x = 194-300), so the lane interiors
of two members line up to within a few pixels and their background grain matches directly.

Method
  1. Lane boxes: pairs of long dark (black, or grey and >= 40 levels darker than their surroundings) vertical lines 35-260 px apart (any figure size). The interior is
     resized to 94 x 634 px. Boxes that contain another lane border or a white gap, or whose
     grain is outside TEX (blank, or other structure inside the box), are rejected.
  2. Residual: interior minus a Gaussian blur (sigma 8); the band (darker than its surroundings,
     dilated) is masked; column and row means are removed (frame shading and scan lines would
     otherwise correlate between unrelated lanes); scaled to unit variance.
  3. Against each exemplar (Thermo images of known pattern-A members): best whole-pixel shift within
     +-3 px, then (a) residual correlation and (b) share of 31 x 31 windows correlating above 0.3.
     Median over the 5 best exemplars.
  Hit: window share >= 0.3.

Validation (Thermo images of 23 Richardson pattern-A members, leave-one-out): all 23 found (window share
0.54-0.97, correlation 0.28-0.56). The aligned correlation falls from 0.66 to below 0.12 when the lanes
are shifted by 8 px, so the match is the grain itself, not JPEG blocks or the frame. 5,851 unflagged PA5
blots in the template ranges: highest window share outside the hits 0.024. Not detected: a member's
second, differently laid-out image (299 x 400, a different blot), and pattern-A figures in other layouts.

    python pilot/pattern_a.py scan SCRAPED_DIR --members MEMBERS_DIR --member-list members.txt --out hits.json
    python pilot/pattern_a.py validate --members MEMBERS_DIR --member-list members.txt
(SCRAPED_DIR / MEMBERS_DIR: scrape_vendors.py output, scraped.jsonl + images/)
"""
import argparse, json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

LW, LH = 94, 634
SHIFT = 3
WIN, WIN_THR = 31, 0.3
HIT_SHARE = 0.3
TEX = (1.0, 8.0)     # grain strength (residual std, gray levels) of a usable lane
TOP = 5


def lanes(path):
    """[(box, gray interior LW x LH)] for every single-lane box in the figure."""
    try: g = np.asarray(Image.open(path).convert("L")).astype(np.float32)
    except Exception: return []
    H, W = g.shape; dark = g < 70; out = []
    fx = dark[int(.06 * H):int(.94 * H)].mean(0)
    # border columns: black lines, or grey lines >= 40 levels darker than the columns 6 px to each side
    col = np.median(g[int(.06 * H):int(.94 * H)], 0); pad = np.pad(col, 6, mode="edge")
    rel = (np.minimum(pad[:-12], pad[12:]) - col >= 40) & (col < 170)
    xs = np.where((fx > 0.8) | rel)[0]
    if len(xs) < 2: return []
    groups = np.split(xs, np.where(np.diff(xs) > 2)[0] + 1); cs = [(q.min(), q.max()) for q in groups]
    for (a0, a1), (b0, b1) in zip(cs, cs[1:]):
        if not 35 <= b0 - a1 <= 260: continue
        fy = dark[:, a1 + 3:b0 - 3].mean(1); ys = np.where(fy > 0.8)[0]
        t, b = (ys.min(), ys.max()) if len(ys) >= 2 and ys.max() - ys.min() > 0.5 * H else (int(.012 * H), int(.988 * H))
        c = g[t + 6:b - 5, a1 + 6:b0 - 5]
        if c.shape[0] < 200 or c.shape[1] < 20: continue
        c = cv2.resize(c, (LW, LH), interpolation=cv2.INTER_AREA)
        if ((c < 70).mean(0) > 0.5).mean() >= 0.03 or (np.median(c, 0) > 245).mean() >= 0.05: continue   # not one lane
        lo = cv2.GaussianBlur(c, (0, 0), 8); band = cv2.dilate((c < lo - 25).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
        tex = float((c - lo)[~band].std())
        if not TEX[0] <= tex <= TEX[1]: continue        # members: 2.2-5.6; >8 = structure (other lanes, edges) inside the box
        out.append(((int(a1), int(b0), int(t), int(b)), c))
    return out


def residual(c):
    lo = cv2.GaussianBlur(c, (0, 0), 8); r = c - lo
    band = cv2.dilate((c < lo - 25).astype(np.uint8), np.ones((25, 25), np.uint8)) > 0
    r[band] = 0
    cm = np.array([r[~band[:, j], j].mean() if (~band[:, j]).sum() > 20 else 0 for j in range(r.shape[1])], np.float32)
    rm = np.array([r[i, ~band[i]].mean() if (~band[i]).sum() > 20 else 0 for i in range(r.shape[0])], np.float32)
    r = r - cm[None, :] - rm[:, None]; r[band] = 0
    return (r / max(r[~band].std(), 1e-3)).astype(np.float32), ~band


def compare(a, b):
    """(correlation, window share) at the best whole-pixel shift within +-SHIFT."""
    (ra, ma), (rb, mb) = a, b; best = None
    for dy in range(-SHIFT, SHIFT + 1):
        for dx in range(-SHIFT, SHIFT + 1):
            sa = (slice(max(0, dy), LH + min(0, dy)), slice(max(0, dx), LW + min(0, dx)))
            sb = (slice(max(0, -dy), LH + min(0, -dy)), slice(max(0, -dx), LW + min(0, -dx)))
            m = ma[sa] & mb[sb]
            if m.sum() < 2000: continue
            x, y = ra[sa][m], rb[sb][m]; v = float((x * y).mean() / (x.std() * y.std() + 1e-6))
            if best is None or v > best[0]: best = (v, ra[sa], rb[sb], m)
    if best is None: return -1.0, 0.0
    v, A, B, m = best; n = ok = 0
    for y in range(0, A.shape[0] - WIN, 16):
        for x in (0, (A.shape[1] - WIN) // 2, A.shape[1] - WIN):
            mm = m[y:y + WIN, x:x + WIN]
            if mm.mean() < 0.7: continue
            p, q = A[y:y + WIN, x:x + WIN][mm], B[y:y + WIN, x:x + WIN][mm]
            if p.std() < 1e-3 or q.std() < 1e-3: continue
            n += 1; ok += float(np.corrcoef(p, q)[0, 1]) > WIN_THR
    return v, (ok / n if n else 0.0)


EX = None
def _init(ex): global EX; EX = ex


def score_lane(c, exclude=None):
    r = residual(c)
    res = sorted((compare(r, e) + (k,) for k, e in EX if k != exclude), key=lambda t: -t[1])[:TOP]
    return float(np.median([t[0] for t in res])), float(np.median([t[1] for t in res])), res[0][2]


def _work(args):
    path, exclude = args; best = None
    for box, c in lanes(path):
        corr, share, ex = score_lane(c, exclude)
        if best is None or share > best["share"]: best = {"box": box, "corr": round(corr, 3), "share": round(share, 3), "best_exemplar": ex}
    return best


def exemplars(members_dir, member_list):
    keep = set(Path(member_list).read_text().split()); ex = []
    for r in map(json.loads, (members_dir / "scraped.jsonl").read_text().splitlines()):
        if r["catalog"] not in keep: continue
        p = members_dir / "images" / r["file"]
        try:
            if Image.open(p).size != (650, 650): continue
        except Exception: continue
        for box, c in lanes(p):
            if abs(box[0] - 194) <= 4 and abs(box[1] - 300) <= 4: ex.append((r["catalog"], residual(c)))
    return ex


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("mode", choices=["scan", "validate"]); ap.add_argument("scraped", nargs="?", type=Path)
    ap.add_argument("--members", type=Path, required=True); ap.add_argument("--member-list", type=Path, required=True)
    ap.add_argument("--out", type=Path); ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(); ex = exemplars(a.members, a.member_list)
    print(f"{len(ex)} exemplar lanes from {len({k for k, _ in ex})} members", flush=True)
    if a.mode == "validate": src, excl = a.members, True
    else: src, excl = a.scraped, False
    recs = [json.loads(l) for l in (src / "scraped.jsonl").read_text().splitlines() if l.strip()]
    if excl:
        keep = set(a.member_list.read_text().split()); recs = [r for r in recs if r["catalog"] in keep]
    jobs = [(str(src / "images" / r["file"]), r["catalog"] if excl else None) for r in recs]
    with ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(ex,)) as pool: res = list(pool.map(_work, jobs, chunksize=16))
    out = [{**{k: r[k] for k in ("catalog", "file") if k in r}, "image_url": r.get("image_url"), **(x or {"share": None})} for r, x in zip(recs, res)]
    hits = [o for o in out if (o.get("share") or 0) >= HIT_SHARE]
    if a.out: a.out.write_text(json.dumps(out, indent=1))
    print(f"{len(out)} images, {sum(o.get('share') is not None for o in out)} with a single-lane box, {len(hits)} hits "
          f"({len({o['catalog'] for o in hits})} products)")
    for o in sorted(out, key=lambda o: -(o.get("share") or -1))[:40]: print(o.get("share"), o.get("corr"), o["catalog"], o.get("best_exemplar"))


if __name__ == "__main__":
    main()

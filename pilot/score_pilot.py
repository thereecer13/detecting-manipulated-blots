import json, random, sys
from pathlib import Path
import numpy as np
S = Path(sys.argv[1]); RES = Path(sys.argv[2]); key = {k["id"]: k for k in json.loads((S / "pilot_key/key.json").read_text())}
preds = {}
for f in sorted((RES).glob("*.json")):
    for p in json.loads(f.read_text()): preds[p["id"]] = p
def auc(s, y):
    s, y = np.array(s), np.array(y); p, n = s[y == 1], s[y == 0]
    return float((p[:, None] > n).mean() + 0.5 * (p[:, None] == n).mean())
def f1(yt, yp):
    tp = sum(a and b for a, b in zip(yt, yp)); fp = sum((not a) and b for a, b in zip(yt, yp)); fn = sum(a and not b for a, b in zip(yt, yp))
    pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return (2 * pr * rc / (pr + rc) if pr + rc else 0), pr, rc, tp, fp, fn
def boot(fn, items, n=2000):
    r = random.Random(0); v = [fn([items[r.randrange(len(items))] for _ in items]) for _ in range(n)]
    return np.percentile(v, [2.5, 97.5])
def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x1 - x0) * max(0, y1 - y0); u = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i
    return i / u if u > 0 else 0
for task, vk, pk, pos in [("A_biofors", "verdict", "probability_manipulated", "manipulated"),
                          ("B_biofors", "verdict", "probability_shared", "shared_content"),
                          ("R_recall", "verdict", "probability_manipulated", "manipulated")]:
    ids = [i for i, k in key.items() if k["task"] == task]; got = [i for i in ids if i in preds]
    print(f"\n== {task}: {len(got)}/{len(ids)} judged")
    if not got: continue
    y = [key[i]["label"] for i in got]; yp = [preds[i][vk] == pos for i in got]; s = [preds[i][pk] for i in got]
    F, pr, rc, tp, fp, fn = f1(y, yp)
    print(f"verdict: F1 {F:.2f} precision {pr:.2f} recall {rc:.2f}  (TP {tp} FP {fp} FN {fn} TN {len(got)-tp-fp-fn})")
    if len(set(y)) == 2:
        items = list(zip(y, s)); lo, hi = boot(lambda it: auc([b for a, b in it], [a for a, b in it]) if len({a for a, b in it}) == 2 else 0.5, items)
        print(f"AUC {auc(s, y):.2f} [95% CI {lo:.2f}-{hi:.2f}]")
        best = max(((f1(y, [v >= t for v in s])[0], t) for t in sorted(set(s))), default=(0, 0))
        print(f"best F1 over thresholds (optimistic, in-sample): {best[0]:.2f} at p>={best[1]}")
        lo, hi = boot(lambda it: f1([a for a, b in it], [b for a, b in it])[0], list(zip(y, yp)))
        print(f"verdict F1 95% CI {lo:.2f}-{hi:.2f}")
    if task == "A_biofors":
        for t in ["idd", "cstd"]:
            sub = [i for i in got if t in key[i].get("types", [])]
            print(f"  recall on {t}: {sum(preds[i][vk]==pos for i in sub)}/{len(sub)}")
        tpi = [i for i in got if key[i]["label"] and preds[i][vk] == pos]
        hit = sum(any(iou(r, b) >= 0.1 for r in preds[i].get("regions", []) for b in key[i]["boxes_frac"]) for i in tpi)
        print(f"  localization: {hit}/{len(tpi)} true positives point at a ground-truth box (IoU>=0.1)")
    if task == "R_recall":
        for i in got: print(f"  {preds[i][vk][:5]} p={preds[i][pk]:.2f} | truth: {key[i]['summary'][:60]}")

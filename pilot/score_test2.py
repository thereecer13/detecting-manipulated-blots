import json, glob, random, sys
import numpy as np
S = sys.argv[1]
key = {k["id"]: k for k in json.load(open(f"{S}/test2_key/key.json"))}
def load(c):
    d = {}
    for f in glob.glob(f"{S}/test2/runs/{c}/*.json"):
        for x in json.load(open(f)): d[x["id"]] = x
    return d
def f1(y, p):
    tp = sum(a and b for a, b in zip(y, p)); fp = sum(b and not a for a, b in zip(y, p)); fn = sum(a and not b for a, b in zip(y, p))
    pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return (2 * pr * rc / (pr + rc) if pr + rc else 0), pr, rc, tp, fp, fn
def auc(s, y):
    s, y = np.array(s), np.array(y); p, n = s[y == 1], s[y == 0]
    return float((p[:, None] > n).mean() + 0.5 * (p[:, None] == n).mean())
def iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    i = max(0, x1 - x0) * max(0, y1 - y0); u = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i
    return i / u if u > 0 else 0
A = [i for i, k in key.items() if k["task"] == "A_biofors"]; R = [i for i, k in key.items() if k["task"] == "R_recall"]
y = [key[i]["label"] for i in A]
runs = {c: load(c) for c in ["baseline", "rules_text", "rules_tools"]}
M = lambda d, i: d[i]["verdict"] == "manipulated"
rng = random.Random(0)
print(f"{'condition':14s} {'F1':>5s} {'prec':>5s} {'rec':>5s}  TP FP FN TN  {'AUC':>5s}  F1 95% CI     loc  IDD  CSTD  Richardson")
for c, d in runs.items():
    p = [M(d, i) for i in A]; s = [d[i]["probability_manipulated"] for i in A]
    F, pr, rc, tp, fp, fn = f1(y, p)
    bs = []
    for _ in range(2000):
        idx = [rng.randrange(60) for _ in range(60)]; bs.append(f1([y[j] for j in idx], [p[j] for j in idx])[0])
    tpi = [i for i in A if key[i]["label"] and M(d, i)]
    loc = sum(any(iou(r, b) >= 0.1 for r in d[i]["regions"] for b in key[i]["boxes_frac"]) for i in tpi)
    idd = [i for i in A if "idd" in key[i]["types"]]; cst = [i for i in A if "cstd" in key[i]["types"]]
    print(f"{c:14s} {F:5.2f} {pr:5.2f} {rc:5.2f}  {tp:2d} {fp:2d} {fn:2d} {60-tp-fp-fn:2d}  {auc(s, y):5.2f}  {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f}  {loc:2d}/{len(tpi):<2d} {sum(M(d,i) for i in idd)}/{len(idd)}  {sum(M(d,i) for i in cst)}/{len(cst)}  {sum(M(d,i) for i in R)}/20")
# paired comparisons vs baseline (McNemar on correctness)
b = runs["baseline"]
for c in ["rules_text", "rules_tools"]:
    d = runs[c]
    better = sum((M(d, i) == bool(key[i]["label"])) and (M(b, i) != bool(key[i]["label"])) for i in A)
    worse = sum((M(d, i) != bool(key[i]["label"])) and (M(b, i) == bool(key[i]["label"])) for i in A)
    from math import comb
    n = better + worse; k = min(better, worse)
    pval = min(1, 2 * sum(comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1
    print(f"{c} vs baseline on BioFors: fixed {better}, broke {worse} (exact McNemar p = {pval:.2f})")
# rules-alone, for comparison
p = [k["flags"]["dup_pairs"] >= 1 or k["flags"]["lines"] >= 1 or k["flags"]["flat_patches"] >= 1 for k in (key[i] for i in A)]
F, pr, rc, tp, fp, fn = f1(y, p)
print(f"{'rules alone':14s} {F:5.2f} {pr:5.2f} {rc:5.2f}  {tp:2d} {fp:2d} {fn:2d} {60-tp-fp-fn:2d}")

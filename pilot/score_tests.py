import json, glob, random, sys
from math import comb
import numpy as np
S = sys.argv[1]; T = sys.argv[2] if len(sys.argv) > 2 else "test3"
CONDS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["baseline", "rules_v1", "rules_v2"]
NOT_BLOT = {"test3": {"5369e56079", "1d1ab6231c"}, "test4": {"0ab79f9ca0", "0202e12482"}}.get(T, set())   # test 3: immunofluorescence panels that slipped into the Richardson set
key = {k["id"]: k for k in json.load(open(f"{S}/{T}_key/key.json"))}
for k in key.values():
    if k["task"] == "V_vendor":   # real vendor blots: group by catalog number, type from Richardson's summary
        k["paper"] = k["catalog"]
        k["types"] = (["painting"] if "paint" in k["summary"].lower() else ["other"]) if k["label"] else []
def load(c):
    d = {}
    for f in glob.glob(f"{S}/{T}/runs/{c}/*.json"):
        for x in json.load(open(f)): d[x["id"]] = x
    return d
def f1(y, p):
    tp = sum(a and b for a, b in zip(y, p)); fp = sum(b and not a for a, b in zip(y, p)); fn = sum(a and not b for a, b in zip(y, p))
    pr = tp / (tp + fp) if tp + fp else 0; rc = tp / (tp + fn) if tp + fn else 0
    return (2 * pr * rc / (pr + rc) if pr + rc else 0), pr, rc, tp, fp, fn
def auc(s, y):
    s, y = np.array(s), np.array(y); p, n = s[y == 1], s[y == 0]
    return float((p[:, None] > n).mean() + 0.5 * (p[:, None] == n).mean())
A = [i for i, k in key.items() if k["task"] in ("A_biofors", "V_vendor")]
R = [i for i, k in key.items() if k["task"] == "R_recall" and i not in NOT_BLOT]
y = [key[i]["label"] for i in A]
runs = {c: load(c) for c in CONDS}
M = lambda d, i: d[i]["verdict"] == "manipulated"
papers = sorted({key[i]["paper"] for i in A})
rng = random.Random(0)
print(f"{'condition':10s} {'F1':>5s} {'prec':>5s} {'rec':>5s}  TP FP FN TN  {'AUC':>5s}  F1 95% CI (by paper) | recall by type | Richardson")
for c, d in runs.items():
    if not all(i in d for i in A): print(c, "incomplete"); continue
    p = [M(d, i) for i in A]; s = [d[i]["probability_manipulated"] for i in A]
    F, pr, rc, tp, fp, fn = f1(y, p)
    bs = []
    for _ in range(2000):
        pick = [rng.choice(papers) for _ in papers]; idx = [j for pp in pick for j, i in enumerate(A) if key[i]["paper"] == pp]
        bs.append(f1([y[j] for j in idx], [p[j] for j in idx])[0])
    kinds = sorted({t for i in A for t in key[i]["types"]})
    bytype = "  ".join(f"{t} {sum(M(d,i) for i in A if t in key[i]['types'])}/{sum(t in key[i]['types'] for i in A)}" for t in kinds)
    rp = [i for i in R if "paint" in key[i]["summary"].lower()]; ro = [i for i in R if i not in rp]
    rtxt = "n/a" if not R else f"{sum(M(d,i) for i in rp)}/{len(rp)} / {sum(M(d,i) for i in ro)}/{len(ro)}" if all(i in d for i in R) else "pending"
    n = len(A)
    print(f"{c:10s} {F:5.2f} {pr:5.2f} {rc:5.2f}  {tp:2d} {fp:2d} {fn:2d} {len(A)-tp-fp-fn:2d}  {auc(s, y):5.2f}  {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f}  | {bytype} | Richardson paint/other {rtxt}")
b = runs["baseline"]
for c in CONDS[1:]:
    d = runs[c]
    if not all(i in d for i in A): continue
    better = sum((M(d, i) == bool(key[i]["label"])) and (M(b, i) != bool(key[i]["label"])) for i in A)
    worse = sum((M(d, i) != bool(key[i]["label"])) and (M(b, i) == bool(key[i]["label"])) for i in A)
    n = better + worse; k = min(better, worse)
    pval = min(1, 2 * sum(comb(n, j) for j in range(k + 1)) / 2 ** n) if n else 1
    print(f"{c} vs baseline on BioFors: fixed {better}, broke {worse} (exact McNemar p = {pval:.2f})")

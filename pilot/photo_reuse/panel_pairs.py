"""Score every pair of named panels of one figure on the greyscale photograph only (colour overlay left out),
best over shifts and a few scales.   pairs.py FIGURE spec.json   spec: {"panels": {"name": [x0,y0,x1,y1]}, "R": 16, "scales": [...], "thr": 60}"""
import sys, json, itertools, cv2, numpy as np
im = cv2.imread(sys.argv[1]); sp = json.load(open(sys.argv[2])); R = sp.get("R", 16); SC = sp.get("scales", [1.0]); thr = sp.get("thr", 60)
def prep(p):
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV); g = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return g, cv2.dilate((hsv[..., 1] > 70).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
def score(pa, pb):
    ga, ca = prep(pa); best = (-2,)
    for s in SC:
        q = pb if s == 1 else cv2.resize(pb, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC); gb, cb = prep(q)
        for dy in range(-R, R + 1, 1):
            for dx in range(-R, R + 1, 1):
                ya0, yb0 = max(0, dy), max(0, -dy); xa0, xb0 = max(0, dx), max(0, -dx)
                h = min(ga.shape[0] - ya0, gb.shape[0] - yb0); w = min(ga.shape[1] - xa0, gb.shape[1] - xb0)
                if h < 20 or w < 20: continue
                a = ga[ya0:ya0 + h, xa0:xa0 + w]; b = gb[yb0:yb0 + h, xb0:xb0 + w]
                m = ~(ca[ya0:ya0 + h, xa0:xa0 + w] | cb[yb0:yb0 + h, xb0:xb0 + w]) & ((a > thr) | (b > thr))
                if m.sum() < 0.3 * ga.size: continue
                x, y = a[m] - a[m].mean(), b[m] - b[m].mean(); d = np.sqrt((x * x).sum() * (y * y).sum())
                c = float((x * y).sum() / d) if d > 0 else -2
                if c > best[0]: best = (c, s, dx, dy)
    return best
P = {k: im[b[1]:b[3], b[0]:b[2]] for k, b in sp["panels"].items()}; res = []
for a, b in itertools.combinations(P, 2):
    r = score(P[a], P[b]); res.append((r[0], a, b, r[1:]))
res.sort(reverse=True); v = [r[0] for r in res]
print("pairs %d  median %.2f  p90 %.2f" % (len(v), np.median(v), np.percentile(v, 90)))
for r in res[:int(sp.get("show", 10))]: print("  %.3f  %s  vs  %s   scale/shift %s" % r)

"""PMC8201856 Fig 5b: compare every mouse panel with every other one.

The 15 panels (3 days x 5 groups) all show four white mice in the same holder on the same dark stage,
so two different photographs already look alike. To separate 'same holder' from 'same photograph',
each pair of panels is aligned by the best shift (within +-14 px) and scored on the greyscale
photograph only: pixels carrying the colour signal overlay in either panel are left out, and the score
is the correlation over the animals and their tails (pixels brighter than the stage in either panel).

    python3 panel_matrix.py FIGURE.jpg OUTDIR
"""
import sys, json, itertools
from pathlib import Path
import cv2
import numpy as np

fig, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = cv2.imread(fig)
ROWS = [(203, 301), (303, 398), (400, 503)]; COLS = [(28, 152), (154, 275), (277, 400), (403, 526), (528, 650)]
DAYS = ["D0", "D7", "D14"]; GROUPS = ["PBS", "aPD-L1", "BPQDs+NIR", "BBPQDs+NIR", "BBPQDs+NIR+aPD-L1"]
names, pans = [], []
for (r, (y0, y1)), (c, (x0, x1)) in itertools.product(enumerate(ROWS), enumerate(COLS)):
    names.append(f"{DAYS[r]} {GROUPS[c]}"); pans.append(im[y0 + 2:y1 - 2, x0 + 2:x1 - 2])
Hc = min(p.shape[0] for p in pans); Wc = min(p.shape[1] for p in pans)


def prep(p):
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV); g = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY).astype(np.float32)
    colour = cv2.dilate((hsv[..., 1] > 70).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0      # signal overlay
    return g, colour


P = [prep(p) for p in pans]


def score(i, j, R=14):
    (ga, ca), (gb, cb) = P[i], P[j]; best = (-2, 0, 0, 0)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            ya0, yb0 = max(0, dy), max(0, -dy); xa0, xb0 = max(0, dx), max(0, -dx)
            h = min(ga.shape[0] - ya0, gb.shape[0] - yb0); w = min(ga.shape[1] - xa0, gb.shape[1] - xb0)
            a = ga[ya0:ya0 + h, xa0:xa0 + w]; b = gb[yb0:yb0 + h, xb0:xb0 + w]
            m = ~(ca[ya0:ya0 + h, xa0:xa0 + w] | cb[yb0:yb0 + h, xb0:xb0 + w]) & ((a > 95) | (b > 95))
            m[:22] = False                     # leave out the holder bar at the top of every panel
            if m.sum() < 400: continue
            x, y = a[m] - a[m].mean(), b[m] - b[m].mean(); d = np.sqrt((x * x).sum() * (y * y).sum())
            c = float((x * y).sum() / d) if d > 0 else -2
            if c > best[0]: best = (c, dx, dy, int(m.sum()))
    return best


n = len(pans); C = np.eye(n); S = {}
for i in range(n):
    for j in range(i + 1, n):
        c, dx, dy, npx = score(i, j); C[i, j] = C[j, i] = c; S[(i, j)] = (c, dx, dy, npx)
off = np.array([C[i, j] for i in range(n) for j in range(i + 1, n)])
print("pairs: %d   median %.2f   90th pct %.2f   max %.2f" % (len(off), np.median(off), np.percentile(off, 90), off.max()))
top = sorted(S.items(), key=lambda kv: -kv[1][0])[:12]
for (i, j), (c, dx, dy, npx) in top: print("  %.3f  %-22s vs %-22s shift (%d,%d)" % (c, names[i], names[j], dx, dy))
json.dump({"panels": names, "matrix": np.round(C, 3).tolist(), "median": float(np.median(off)), "p90": float(np.percentile(off, 90)),
           "top": [{"a": names[i], "b": names[j], "corr": round(c, 3), "shift": [dx, dy]} for (i, j), (c, dx, dy, npx) in top]},
          open(out / "panel_matrix.json", "w"), indent=1)
# picture of the matrix
cell = 46; pad = 210; img = np.full((pad + n * cell + 10, pad + n * cell + 10, 3), 255, np.uint8)
for i in range(n):
    cv2.putText(img, names[i], (6, pad + i * cell + 29), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
    t = np.full((cell, pad, 3), 255, np.uint8); cv2.putText(t, names[i], (4, 29), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
    t = cv2.rotate(t, cv2.ROTATE_90_COUNTERCLOCKWISE); img[0:pad, pad + i * cell:pad + (i + 1) * cell] = t
    for j in range(n):
        v = C[i, j]; col = (255, 255, 255) if i == j else tuple(int(x) for x in cv2.applyColorMap(np.uint8([[int(np.clip((v - 0.3) / 0.7, 0, 1) * 255)]]), cv2.COLORMAP_VIRIDIS)[0, 0])
        cv2.rectangle(img, (pad + j * cell, pad + i * cell), (pad + (j + 1) * cell - 2, pad + (i + 1) * cell - 2), col, -1)
        if i != j: cv2.putText(img, "%.2f" % v, (pad + j * cell + 4, pad + i * cell + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255) if v < 0.8 else (0, 0, 0), 1, cv2.LINE_AA)
cv2.imwrite(str(out / "PMC8201856_Fig5b_panel_matrix.png"), img)

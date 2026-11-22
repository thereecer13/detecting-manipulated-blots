"""Blog figure: three 'healing' photographs that are one photograph with the wound shortened."""
import sys, json, cv2, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
im = cv2.imread(sys.argv[1]); meas = json.load(open(sys.argv[2]))["wound"]
COLS = {"A": (1, 234), "B": (237, 471), "C": (474, 707)}; ROWS = (35, 269)
DAY = {"A": "day 3", "B": "day 7", "C": "day 14"}
pan = {k: im[ROWS[0]:ROWS[1], x0:x1] for k, (x0, x1) in COLS.items()}
sift = cv2.SIFT_create(nfeatures=30000, contrastThreshold=0.004, edgeThreshold=30); K = {}
for k, p in pan.items():
    g = cv2.resize(cv2.cvtColor(p, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    kp, de = sift.detectAndCompute(g, None); K[k] = (np.array([q.pt for q in kp], np.float32) / 3, de)
bf = cv2.BFMatcher(cv2.NORM_L2); T = {"A": np.array([[1, 0, 0], [0, 1, 0]], float)}
for k in "BC":
    (xa, da), (xb, db) = K[k], K["A"]; src, dst = [], []
    for m, n in bf.knnMatch(da, db, k=2):
        if m.distance < 0.85 * n.distance: src.append(xa[m.queryIdx]); dst.append(xb[m.trainIdx])
    T[k], _ = cv2.estimateAffine2D(np.array(src), np.array(dst), method=cv2.RANSAC, ransacReprojThreshold=1.5, maxIters=50000, confidence=0.999)
S = 8; X0, Y0, X1, Y1 = 52, 74, 172, 134      # close-up window in A's frame
def close(k):
    M = T[k].copy(); M[:, 2] -= (X0, Y0); M *= S
    return cv2.cvtColor(cv2.warpAffine(pan[k], M, ((X1 - X0) * S, (Y1 - Y0) * S), flags=cv2.INTER_CUBIC, borderValue=(150, 150, 150)), cv2.COLOR_BGR2RGB)
ca, cb = "#2a78d6", "#d95f02"
ARROWS = {"B": [((528, 690), (330, 830))], "C": [((656, 318), (700, 600)), ((250, 430), (300, 760))]}   # 4x panel pixels
fig = plt.figure(figsize=(13, 8.6), facecolor="#fcfcfb")
gs = fig.add_gridspec(2, 3, height_ratios=[2, 1], hspace=0.16, wspace=0.05, left=0.03, right=0.97, top=0.86, bottom=0.1)
for i, k in enumerate("ABC"):
    ax = fig.add_subplot(gs[0, i]); ax.imshow(cv2.cvtColor(cv2.resize(pan[k], None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)); ax.axis("off")
    ax.set_title(f"Published as {DAY[k]}", fontsize=17, pad=8)
    for tip, tail in ARROWS.get(k, []):      # where the fur texture has been smoothed away
        ax.annotate("smoothed", xy=tip, xytext=tail, fontsize=13, fontweight="bold", color="#1a1a1a", ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="none", alpha=0.85),
                    arrowprops=dict(arrowstyle="-|>", color="#1a1a1a", lw=2.5, mutation_scale=22, shrinkA=2, shrinkB=0))
    ax = fig.add_subplot(gs[1, i]); ax.imshow(close(k)); ax.set_xticks([]); ax.set_yticks([])
    w = meas[k]; xl = (meas["A"]["left_end_in_A"][0] - X0) * S; xr = (w["right_end_in_A"][0] - X0) * S
    ax.axvline(xl, color=ca, lw=2.5); ax.axvline(xr, color=cb, lw=2.5)
    ax.set_title(f"Wound {w['length_cm']:.1f} cm by the ruler", fontsize=15, pad=6)
fig.suptitle("Three stages of healing, one photograph", fontsize=23, fontweight="bold", y=0.965)
fig.text(0.5, 0.035, "Bottom row: the three panels enlarged and aligned on the ruler. The ruler, glove and animal line up exactly, so all three are one photograph.\n"
         "Only the wound differs: its left end (blue) stays at the same pixel while its right end (orange) moves in, and the fur around it is smoothed (arrows).",
         ha="center", fontsize=12.5, color="#444")
fig.savefig(sys.argv[3], dpi=160, facecolor=fig.get_facecolor())

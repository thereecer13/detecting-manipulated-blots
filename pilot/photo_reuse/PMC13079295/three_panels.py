"""PMC13079295 Fig 5, panels A (day 3), B (day 7), C (day 14): are they one photograph?

Registers B and C onto A (keypoints + RANSAC, similarity and full affine), measures the red wound in
each panel in A's frame, compares fine texture by region, and writes an annotated figure and a blink GIF.

    python3 three_panels.py FIGURE.jpg OUTDIR
"""
import sys, json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

fig, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = cv2.imread(fig)
COLS = {"A": (1, 234), "B": (237, 471), "C": (474, 707)}; ROWS = (35, 269)        # the three photographs
DAY = {"A": "day 3", "B": "day 7", "C": "day 14"}
pan = {k: im[ROWS[0]:ROWS[1], x0:x1] for k, (x0, x1) in COLS.items()}
H, W = pan["A"].shape[:2]

# --- registration -------------------------------------------------------------------------------
sift = cv2.SIFT_create(nfeatures=30000, contrastThreshold=0.004, edgeThreshold=30); K = {}
for k, p in pan.items():
    g = cv2.resize(cv2.cvtColor(p, cv2.COLOR_BGR2GRAY), None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    kp, de = sift.detectAndCompute(g, None); K[k] = (np.array([q.pt for q in kp], np.float32) / 3, de)
bf = cv2.BFMatcher(cv2.NORM_L2); T = {"A": np.array([[1, 0, 0], [0, 1, 0]], float)}; reg = {}
for k in "BC":
    (xa, da), (xb, db) = K[k], K["A"]; src, dst = [], []
    for m, n in bf.knnMatch(da, db, k=2):
        if m.distance < 0.85 * n.distance: src.append(xa[m.queryIdx]); dst.append(xb[m.trainIdx])
    src, dst = np.array(src), np.array(dst)
    Ms, ins = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.5, maxIters=50000, confidence=0.999)
    Ma, ina = cv2.estimateAffine2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.5, maxIters=50000, confidence=0.999)
    T[k] = Ma
    reg[k] = {"matches": len(src), "zoom_only_inliers": int(ins.sum()), "affine_inliers": int(ina.sum()),
              "x_scale": round(float(np.hypot(Ma[0, 0], Ma[1, 0])), 3), "y_scale": round(float(np.hypot(Ma[0, 1], Ma[1, 1])), 3)}

# --- the wound in each panel, in A's frame ------------------------------------------------------
def red(p):
    b, g, r = [p[..., i].astype(int) for i in range(3)]
    return cv2.morphologyEx(((r - g > 22) & (r - b > 10) & (g < 115)).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
PX_PER_CM = 21.0      # ruler digits 1 and 7 in panel A are 126 px apart
wound = {}
for k, p in pan.items():
    n, lab, st, _ = cv2.connectedComponentsWithStats(red(p), 8)
    # the wound is the largest red component away from the right edge (the ear and paw are pink)
    i = max((i for i in range(1, n) if st[i][0] + st[i][2] < 200 and st[i][0] > 20), key=lambda i: st[i][4])
    ys, xs = np.where(lab == i); xy = np.stack([xs, ys], 1).astype(float); c = xy.mean(0)
    ax = np.linalg.svd(xy - c)[2][0]; pr = (xy - c) @ ax; e = sorted([c + ax * pr.min(), c + ax * pr.max()], key=lambda q: q[0])
    a = [T[k][:, :2] @ q + T[k][:, 2] for q in e]; L = float(np.linalg.norm(a[1] - a[0]))
    wound[k] = {"left_end_in_A": [round(float(v), 1) for v in a[0]], "right_end_in_A": [round(float(v), 1) for v in a[1]],
                "length_px": round(L, 1), "length_cm": round(L / PX_PER_CM, 2)}
for k in "ABC": wound[k]["relative_to_A"] = round(wound[k]["length_px"] / wound["A"]["length_px"], 2)

# --- fine texture by region (A's frame) ---------------------------------------------------------
gray = lambda p: cv2.cvtColor(p, cv2.COLOR_BGR2GRAY).astype(np.float32)
al = {k: cv2.warpAffine(gray(pan[k]), T[k].astype(np.float32), (W, H), flags=cv2.INTER_CUBIC) for k in "ABC"}
ok = {k: cv2.warpAffine(np.ones((H, W), np.float32), T[k].astype(np.float32), (W, H), flags=cv2.INTER_NEAREST) > 0.5 for k in "ABC"}
A_lo = cv2.resize(cv2.resize(al["A"], None, fx=1 / 1.2, fy=1 / 1.2, interpolation=cv2.INTER_AREA), (W, H), interpolation=cv2.INTER_CUBIC)   # A at B's resolution
hp = lambda x: x - cv2.GaussianBlur(x, (0, 0), 2.0)
REG = {"fur on the back, left of the wound": (8, 95, 70, 160), "fur at the shoulder": (150, 112, 186, 140), "ruler face": (92, 64, 185, 92),
       "glove": (110, 5, 200, 45), "wall": (5, 8, 85, 60), "table": (25, 200, 110, 228)}
tex = {}
for name, (x0, y0, x1, y1) in REG.items():
    sl = (slice(y0, y1), slice(x0, x1)); row = {}
    if ok["B"][sl].mean() > 0.98: row["B_over_A"] = round(float(hp(al["B"])[sl].std() / hp(A_lo)[sl].std()), 2)
    if ok["C"][sl].mean() > 0.98: row["C_over_A"] = round(float(hp(al["C"])[sl].std() / hp(al["A"])[sl].std()), 2)
    tex[name] = row
json.dump({"registration_onto_A": reg, "wound": wound, "fine_texture_ratio": tex}, open(out / "measurements.json", "w"), indent=1)
print(json.dumps({"registration_onto_A": reg, "wound": wound, "fine_texture_ratio": tex}, indent=1))

# --- figure -------------------------------------------------------------------------------------
Z = 3; S = np.diag([Z, Z, 1.0]); GREY = (150, 150, 150)
def to_A(k):
    M = (S @ np.vstack([T[k], [0, 0, 1]]))[:2]
    return cv2.warpAffine(pan[k], M.astype(np.float32), (W * Z, H * Z), flags=cv2.INTER_CUBIC, borderValue=GREY)
aligned = {k: to_A(k) for k in "ABC"}
font = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
pw, ph, gap, top = W * Z, H * Z, 18, 54
cx0, cy0, cx1, cy1 = 55, 84, 175, 128; cz = (3 * pw + 2 * gap - 2 * gap) / 3 / (cx1 - cx0)     # close-up window in A's frame
ch = int((cy1 - cy0) * cz)
Wd = 3 * pw + 4 * gap; Hd = top + ph + 62 + ph + 62 + ch + 96
cv = Image.new("RGB", (Wd, Hd), "white"); d = ImageDraw.Draw(cv)
d.text((gap, 12), "PMC13079295, Fig 5: the three wound photographs", font=font(26, True), fill="black")
note = {"A": "", "B": "enlarged 1.20x", "C": "squeezed vertically to 81%"}
xL = wound["A"]["left_end_in_A"][0]
for j, k in enumerate("ABC"):
    x = gap + j * (pw + gap); y1 = top; y2 = top + ph + 62; y3 = y2 + ph + 62
    d.text((x, y1 - 2 + ph + 6), f"{k}: labelled {DAY[k]}, as published", font=font(20), fill="black")
    cv.paste(Image.fromarray(cv2.cvtColor(cv2.resize(pan[k], (pw, ph), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)), (x, y1))
    cv.paste(Image.fromarray(cv2.cvtColor(aligned[k], cv2.COLOR_BGR2RGB)), (x, y2))
    d.text((x, y2 + ph + 6), f"{k} placed in A's frame" + (f" ({note[k]})" if note[k] else " (unchanged)"), font=font(20), fill="black")
    # wound close-up from the aligned image
    M = (np.diag([cz, cz, 1.0]) @ np.array([[1, 0, -cx0], [0, 1, -cy0], [0, 0, 1.0]]) @ np.vstack([T[k], [0, 0, 1]]))[:2]
    cu = cv2.warpAffine(pan[k], M.astype(np.float32), (int((cx1 - cx0) * cz), ch), flags=cv2.INTER_CUBIC, borderValue=GREY)
    cv.paste(Image.fromarray(cv2.cvtColor(cu, cv2.COLOR_BGR2RGB)), (x, y3))
    xl = x + (xL - cx0) * cz; xr = x + (wound[k]["right_end_in_A"][0] - cx0) * cz
    d.line([(xl, y3), (xl, y3 + ch)], fill=(0, 190, 255), width=2); d.line([(xr, y3), (xr, y3 + ch)], fill=(255, 170, 0), width=2)
    d.text((x, y3 + ch + 6), f"wound {wound[k]['length_cm']:.1f} cm by the ruler ({round(100 * wound[k]['relative_to_A'])}% of A)", font=font(20, True), fill="black")
d.text((gap, Hd - 34), "Close-ups: blue line = left end of the wound (same pixel in all three); orange line = right end.", font=font(19), fill="black")
cv.save(out / "PMC13079295_Fig5_three_panels.png")
frames = []
for k in "ABC":
    f = Image.fromarray(cv2.cvtColor(aligned[k], cv2.COLOR_BGR2RGB)); dd = ImageDraw.Draw(f)
    dd.rectangle([0, 0, 330, 34], fill="white"); dd.text((8, 5), f"Panel {k}: labelled {DAY[k]}", font=font(22, True), fill="black"); frames.append(f)
frames[0].save(out / "PMC13079295_Fig5_blink.gif", save_all=True, append_images=frames[1:], duration=900, loop=0)

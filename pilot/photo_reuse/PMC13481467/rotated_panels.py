"""PMC13481467 Fig 5E: the NC+LPS and OE-Vector+LPS transwell images are one field, turned about 107 degrees.

Works on the full-resolution Figure 5 taken from the article PDF in the PMC open-data bucket
(pdfimages -png -f 7 -l 7 PMC13481467.1.pdf p7  ->  p7-000.png, 2056 x 2759 px).
Registers the NC+LPS panel onto the OE-Vector+LPS panel (keypoints + RANSAC, similarity transform), measures
the agreement, and draws a figure for the blog post.

    python3 rotated_panels.py p7-000.png OUTDIR
"""
import sys, json, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = cv2.imread(src)
BOX = {"NC+LPS": (249, 1424, 390, 312), "KO+LPS": (654, 1424, 390, 312), "OE+LPS": (249, 1798, 391, 312), "OE-Vector+LPS": (652, 1797, 393, 313)}   # x, y, w, h
crop = lambda k: im[BOX[k][1]:BOX[k][1] + BOX[k][3], BOX[k][0]:BOX[k][0] + BOX[k][2]]
A, B = crop("NC+LPS"), crop("OE-Vector+LPS")
gA, gB = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)

sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.02)
ka, da = sift.detectAndCompute(gA, None); kb, db = sift.detectAndCompute(gB, None)
pa, pb = [], []
for m, n in cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2):
    if m.distance < 0.75 * n.distance: pa.append(ka[m.queryIdx].pt); pb.append(kb[m.trainIdx].pt)
pa, pb = np.float32(pa), np.float32(pb)
M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=2.0, maxIters=20000, confidence=0.999)
inl = inl.ravel().astype(bool)
scale = math.hypot(M[0, 0], M[1, 0]); angle = math.degrees(math.atan2(M[1, 0], M[0, 0]))
resid = float(np.sqrt((((pa[inl] @ M[:, :2].T + M[:, 2]) - pb[inl]) ** 2).sum(1)).mean())

h, w = gB.shape
WA = cv2.warpAffine(A, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
valid = cv2.warpAffine(np.full(gA.shape, 255, np.uint8), M, (w, h), flags=cv2.INTER_NEAREST) > 0
valid = cv2.erode(valid.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
ga2 = cv2.cvtColor(WA, cv2.COLOR_BGR2GRAY).astype(np.float32); gb2 = gB.astype(np.float32)
x, y = ga2[valid] - ga2[valid].mean(), gb2[valid] - gb2[valid].mean()
ncc = float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))
# control: the same comparison against the other three panels (no transform found, so use the best of 0/90/180/270)
ctrl = {}
for k in ("KO+LPS", "OE+LPS"):
    g = cv2.cvtColor(crop(k), cv2.COLOR_BGR2GRAY).astype(np.float32); best = -1
    for r in range(4):
        t = np.rot90(g, r); hh, ww = min(t.shape[0], h), min(t.shape[1], w)
        u, v = t[:hh, :ww] - t[:hh, :ww].mean(), gb2[:hh, :ww] - gb2[:hh, :ww].mean()
        best = max(best, float((u * v).sum() / np.sqrt((u * u).sum() * (v * v).sum())))
    ctrl[k] = round(best, 3)
res = {"matched_points": int(len(pa)), "inliers": int(inl.sum()), "rotation_deg": round(angle, 1), "scale": round(scale, 3),
       "mean_residual_px": round(resid, 2), "overlap_share_of_OE_Vector_panel": round(float(valid.mean()), 2),
       "pixel_correlation_in_overlap": round(ncc, 3), "best_correlation_other_panels": ctrl}
json.dump(res, open(out / "measurements.json", "w"), indent=1); print(json.dumps(res, indent=1))

# ---- figure -------------------------------------------------------------------------------------
Z = 2.0; RED = (214, 39, 40); BLUE = (31, 119, 180)
font = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
rgb = lambda a: Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
up = lambda a: cv2.resize(a, None, fx=Z, fy=Z, interpolation=cv2.INTER_CUBIC)
# outline of the shared area: B's frame mapped back into A, clipped to A; and A's frame mapped into B, clipped to B
Mi = cv2.invertAffineTransform(M)
def quad(Mx, ww, hh): return (np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]]) @ Mx[:, :2].T + Mx[:, 2])
def clip(poly, ww, hh):
    r, p = cv2.intersectConvexConvex(np.float32(poly), np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])); return p.reshape(-1, 2) if p is not None else np.zeros((0, 2))
inA = clip(quad(Mi, w, h), gA.shape[1], gA.shape[0]); inB = clip(quad(M, gA.shape[1], gA.shape[0]), w, h)
# a few clearly matched cells to mark in both panels (well spread inliers)
pts = np.where(inl)[0]; chosen = []
for i in sorted(pts, key=lambda i: -ka[0].response if False else np.random.RandomState(3).rand()):
    if all(np.hypot(*(pa[i] - pa[j])) > 70 for j in chosen) and 25 < pa[i][0] < gA.shape[1] - 25 and 25 < pa[i][1] < gA.shape[0] - 25 and 25 < pb[i][0] < w - 25 and 25 < pb[i][1] < h - 25: chosen.append(i)
    if len(chosen) == 6: break

pw, ph = int(w * Z), int(h * Z); gap = 40; top = 150; W = 3 * pw + 4 * gap; H = top + ph + 250
cv = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(cv)
d.text((gap, 26), "One field of cells, shown as two different control groups", font=font(40, True), fill="black")
d.text((gap, 82), "Transwell migration assay. Published panels on the left and in the middle; on the right, the first panel turned to match the second.", font=font(22), fill=(70, 70, 70))
def place(col, img, title, sub, colr):
    x = gap + col * (pw + gap); cv.paste(rgb(img), (x, top)); d.rectangle([x - 3, top - 3, x + img.shape[1] + 2, top + img.shape[0] + 2], outline=colr, width=5)
    d.text((x, top + ph + 16), title, font=font(30, True), fill=colr); d.text((x, top + ph + 58), sub, font=font(22), fill="black"); return x
xa = place(0, up(A), "Published as “NC+LPS”", "control for the knockout cells", RED)
xb = place(1, up(B), "Published as “OE-Vector+LPS”", "control for the overexpressing cells", BLUE)
xc = place(2, up(WA), "“NC+LPS” turned %d°" % round(abs(angle)), "lines up with the middle panel, cell for cell", RED)
for x0, poly, colr in ((xa, inA, BLUE), (xb, inB, RED), (xc, inB, BLUE)):
    q = [(x0 + px * Z, top + py * Z) for px, py in poly]; d.line(q + [q[0]], fill=colr, width=4)
for n, i in enumerate(chosen):
    for x0, p in ((xa, pa[i]), (xb, pb[i]), (xc, pb[i])):
        cx, cy = x0 + p[0] * Z, top + p[1] * Z; d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=(255, 200, 0), width=4)
        d.text((cx + 20, cy - 34), str(n + 1), font=font(24, True), fill="black", stroke_width=3, stroke_fill="white")
yb = top + ph + 110
d.text((gap, yb), "Outlined area = the part of the field the two published panels share (%d%% of the panel). Numbered circles mark the same spots in each panel." % round(100 * valid.mean()), font=font(22), fill="black")
d.text((gap, yb + 34), "Pixel agreement after turning: %.2f (the figure’s other two panels against the same image: %.2f and %.2f)." % (ncc, ctrl["KO+LPS"], ctrl["OE+LPS"]), font=font(22), fill="black")
d.text((gap, yb + 84), "Source: Inflamm Res 2026, doi:10.1007/s00011-026-02342-2, Fig. 5E (CC BY 4.0). Panels enlarged; outlines, circles and the turned copy added.", font=font(19), fill=(90, 90, 90))
cv.save(out / "PMC13481467_Fig5E_rotated_reuse.png"); print(cv.size)

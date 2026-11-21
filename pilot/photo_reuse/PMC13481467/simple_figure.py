"""PMC13481467 Fig 5E, simple version: the two published panels, and the first one turned to the matching angle.

    python3 simple_figure.py p7-000.png OUTDIR      (p7-000.png: see rotated_panels.py)
"""
import sys, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = cv2.imread(src)
A = im[1424:1424 + 312, 249:249 + 390]; B = im[1797:1797 + 313, 652:652 + 393]        # NC+LPS, OE-Vector+LPS
gA, gB = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.02)
ka, da = sift.detectAndCompute(gA, None); kb, db = sift.detectAndCompute(gB, None)
pa, pb = [], []
for m, n in cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2):
    if m.distance < 0.75 * n.distance: pa.append(ka[m.queryIdx].pt); pb.append(kb[m.trainIdx].pt)
M, _ = cv2.estimateAffinePartial2D(np.float32(pa), np.float32(pb), method=cv2.RANSAC, ransacReprojThreshold=2.0, maxIters=20000, confidence=0.999)
angle = math.degrees(math.atan2(M[1, 0], M[0, 0]))

Z = 2.0; h, w = gB.shape; S = np.diag([Z, Z, 1.0])
up = lambda a: cv2.resize(a, None, fx=Z, fy=Z, interpolation=cv2.INTER_CUBIC)
# the whole first panel, turned and placed where it lines up with the second panel; canvas grown so nothing is cut off
T = (S @ np.vstack([M, [0, 0, 1]]))[:2]
c = np.float32([[0, 0], [A.shape[1], 0], [A.shape[1], A.shape[0]], [0, A.shape[0]]]) @ T[:, :2].T + T[:, 2]
x0, y0 = np.floor(c.min(0)).astype(int); x1, y1 = np.ceil(c.max(0)).astype(int)
x0, y0 = min(x0, 0), min(y0, 0); x1, y1 = max(x1, int(w * Z)), max(y1, int(h * Z))
T2 = T.copy(); T2[:, 2] -= (x0, y0)
R = cv2.warpAffine(A, T2, (x1 - x0, y1 - y0), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
Bc = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8); Bc[-y0:-y0 + int(h * Z), -x0:-x0 + int(w * Z)] = up(B)   # second panel at the same position

font = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
rgb = lambda a: Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
gap = 50; top = 30; lab = 70
cols = [(up(A), "NC+LPS, as published"), (R, "NC+LPS, turned %d°" % round(abs(angle))), (Bc, "OE-Vector+LPS, as published")]
H = max(c.shape[0] for c, _ in cols); W = sum(c.shape[1] for c, _ in cols) + gap * 4
cv = Image.new("RGB", (W, top + H + lab + 50), "white"); d = ImageDraw.Draw(cv); x = gap
for img, name in cols:
    y = top + (H - img.shape[0]) // 2; cv.paste(rgb(img), (x, y))
    tw = d.textlength(name, font=font(30, True)); d.text((x + (img.shape[1] - tw) / 2, top + H + 14), name, font=font(30, True), fill="black")
    x += img.shape[1] + gap
d.text((gap, top + H + lab + 8), "Inflamm Res 2026, doi:10.1007/s00011-026-02342-2, Fig. 5E (CC BY 4.0). Panels enlarged; middle panel rotated.", font=font(19), fill=(100, 100, 100))
cv.save(out / "PMC13481467_Fig5E_rotated_simple.png"); print(cv.size, round(angle, 1))

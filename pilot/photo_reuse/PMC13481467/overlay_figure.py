"""PMC13481467 Fig 5E, overlay version: NC+LPS as published, the two panels laid over each other (OE-Vector+LPS
turned to the matching angle, both half transparent), and OE-Vector+LPS as published.

    python3 overlay_figure.py p7-000.png OUTDIR [--anon]      (p7-000.png: see rotated_panels.py)

--anon: label the panels "Sample A" and "Sample B", leave out the source line, and write a file name
without the paper's ID (the version used in the blog post).
"""
import sys, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
ANON = "--anon" in sys.argv
NA, NB = ("Sample A", "Sample B") if ANON else ("NC+LPS", "OE-Vector+LPS")
im = cv2.imread(src)
A = im[1424:1424 + 312, 249:249 + 390]; B = im[1797:1797 + 313, 652:652 + 393]        # NC+LPS, OE-Vector+LPS
gA, gB = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY), cv2.cvtColor(B, cv2.COLOR_BGR2GRAY)
sift = cv2.SIFT_create(nfeatures=8000, contrastThreshold=0.02)
ka, da = sift.detectAndCompute(gA, None); kb, db = sift.detectAndCompute(gB, None)
pa, pb = [], []
for m, n in cv2.BFMatcher(cv2.NORM_L2).knnMatch(da, db, k=2):
    if m.distance < 0.75 * n.distance: pa.append(ka[m.queryIdx].pt); pb.append(kb[m.trainIdx].pt)
M, _ = cv2.estimateAffinePartial2D(np.float32(pb), np.float32(pa), method=cv2.RANSAC, ransacReprojThreshold=2.0, maxIters=20000, confidence=0.999)   # OE-Vector -> NC
angle = math.degrees(math.atan2(M[1, 0], M[0, 0]))

Z = 2.0; S = np.diag([Z, Z, 1.0]); ah, aw = gA.shape; AW, AH = int(aw * Z), int(ah * Z)
up = lambda a: cv2.resize(a, None, fx=Z, fy=Z, interpolation=cv2.INTER_CUBIC)
T = (S @ np.vstack([M, [0, 0, 1]]))[:2]
c = np.float32([[0, 0], [B.shape[1], 0], [B.shape[1], B.shape[0]], [0, B.shape[0]]]) @ T[:, :2].T + T[:, 2]
x0, y0 = np.floor(c.min(0)).astype(int); x1, y1 = np.ceil(c.max(0)).astype(int)
x0, y0 = min(x0, 0) - 4, min(y0, 0) - 4; x1, y1 = max(x1, AW) + 4, max(y1, AH) + 4
T2 = T.copy(); T2[:, 2] -= (x0, y0); size = (x1 - x0, y1 - y0)
Rb = cv2.warpAffine(B, T2, size, flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255)).astype(np.float32)
mb = cv2.warpAffine(np.ones(B.shape[:2], np.float32), T2, size, flags=cv2.INTER_LINEAR)[..., None]
Ra = np.full((size[1], size[0], 3), 255, np.float32); ma = np.zeros((size[1], size[0], 1), np.float32)
Ra[-y0:-y0 + AH, -x0:-x0 + AW] = up(A); ma[-y0:-y0 + AH, -x0:-x0 + AW] = 1
# both present: the average of the two; only one present: that image at half strength on white; neither: white
wa = 0.5 * ma; wb = 0.5 * mb
O = wa * Ra + wb * Rb + (1 - wa - wb) * 255
O = np.clip(O, 0, 255).astype(np.uint8)

font = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
rgb = lambda a: Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
gap = 50; top = 20
cols = [(up(A), NA + ", as published"), (O, "Both overlaid (%s turned %d°)" % (NB, round(abs(angle)))), (up(B), NB + ", as published")]
H = max(c.shape[0] for c, _ in cols); W = sum(c.shape[1] for c, _ in cols) + gap * 4
cv = Image.new("RGB", (W, top + H + (70 if ANON else 110)), "white"); d = ImageDraw.Draw(cv); x = gap
for img, name in cols:
    cv.paste(rgb(img), (x, top + (H - img.shape[0]) // 2)); tw = d.textlength(name, font=font(28, True))
    d.text((x + (img.shape[1] - tw) / 2, top + H + 12), name, font=font(28, True), fill="black"); x += img.shape[1] + gap
if not ANON: d.text((gap, top + H + 70), "Inflamm Res 2026, doi:10.1007/s00011-026-02342-2, Fig. 5E (CC BY 4.0). Panels enlarged; middle panel is a half-transparent overlay of the other two.", font=font(19), fill=(100, 100, 100))
cv.save(out / ("rotated_reuse_overlay_anonymized.png" if ANON else "PMC13481467_Fig5E_overlay.png")); print(cv.size, round(angle, 1))

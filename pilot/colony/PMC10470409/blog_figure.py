"""PMC10470409 Fig 7B, blog figure (anonymised, same style as the photo-reuse figures):
Sample A as published | both overlaid, half transparent (Sample B enlarged to match) | Sample B as published.
Colonies present in only one of the two images are circled (red: only in A, blue: only in B).

Inputs are the working files written by big1.py and big2.py from the larger image the user supplied:
bigA.png, bigB.png (the two plates), Mbig.npy (B -> A), onlyA.npy, onlyB.npy (one-sided colonies, A's frame).

    python3 blog_figure.py WORKDIR OUTDIR
"""
import sys, math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

wd, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
A = cv2.imread(str(wd / "bigA.png")); B = cv2.imread(str(wd / "bigB.png")); M = np.load(wd / "Mbig.npy")
oa = np.load(wd / "onlyA.npy"); ob = np.load(wd / "onlyB.npy")            # x, y, area
zoom = math.hypot(M[0, 0], M[1, 0]); Mi = cv2.invertAffineTransform(M)
h, w = A.shape[:2]
Bw = cv2.warpAffine(B, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255)).astype(np.float32)
O = np.clip(0.5 * A.astype(np.float32) + 0.5 * Bw, 0, 255).astype(np.uint8)          # each plate at half strength

RED = (214, 39, 40); BLUE = (31, 119, 180)
font = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
rgb = lambda a: Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))
S = 820                                            # each panel drawn S x S
fit = lambda a: cv2.resize(a, (S, S), interpolation=cv2.INTER_AREA if a.shape[0] > S else cv2.INTER_CUBIC)
kA, kB = S / w, S / B.shape[1]
gap = 60; top = 110; FS = 40
cols = [(fit(A), "Sample A, as published"), (fit(O), "Overlaid (Sample B enlarged %.2f×)" % zoom), (fit(B), "Sample B, as published")]
W = 3 * S + 4 * gap; cv = Image.new("RGB", (W, top + S + 90), "white"); d = ImageDraw.Draw(cv)
xs = []
for i, (img, name) in enumerate(cols):
    x = gap + i * (S + gap); xs.append(x); cv.paste(rgb(img), (x, top)); tw = d.textlength(name, font=font(FS, True))
    d.text((x + (S - tw) / 2, 30), name, font=font(FS, True), fill="black")
def ring(x0, cx, cy, r, col): d.ellipse([x0 + cx - r, top + cy - r, x0 + cx + r, top + cy + r], outline=col, width=4)
for pts, col in ((oa, RED), (ob, BLUE)):
    for x, y, ar in pts:
        r = math.sqrt(ar / math.pi) + 12
        ring(xs[1], x * kA, y * kA, r * kA, col)                                   # overlay (A's frame)
        if col == RED: ring(xs[0], x * kA, y * kA, r * kA, col)                    # only in A: on A
        else:
            bx, by = Mi[:, :2] @ np.array([x, y], float) + Mi[:, 2]; ring(xs[2], bx * kB, by * kB, r / zoom * kB, col)   # only in B: on B
y = top + S + 26; x = gap
for col, txt in ((RED, "colony only in Sample A (%d)" % len(oa)), (BLUE, "colony only in Sample B (%d)" % len(ob))):
    d.ellipse([x, y + 4, x + 30, y + 34], outline=col, width=4); d.text((x + 44, y), txt, font=font(28), fill="black"); x += 44 + d.textlength(txt, font=font(28)) + 70
cv.save(out / "colony_plate_reuse_anonymized.png"); print(cv.size, round(zoom, 3), len(oa), len(ob))

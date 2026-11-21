"""PMC8201856 Fig 5b, blog figure: the two panels of pair A (D0 aPD-L1 and D14 aPD-L1), side by side,
labelled "Time point 1" and "Time point 2" with titles above (anonymised at the user's request: no source).

Uses the full-resolution Figure 5 from the article PDF in the PMC open-data bucket
(pdfimages -png -f 12 -l 12 PMC8201856.1.pdf q12  ->  q12-000.png, 1853 x 2481 px).

    python3 blog_figure.py q12-000.png OUTDIR
"""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
im = cv2.imread(src)
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
# Panel edges in the full-resolution figure. Rows are bounded by the white gutter lines found at
# y = 488-506, 756-757, 997-999, 1261-1281; the aPD-L1 column lies between the thin gutters near x = 384 and 691.
X0, X1 = 384, 692


def panel(y0, y1):
    """The aPD-L1 panel in rows y0..y1, trimmed to the columns and rows that are not gutter (bright lines)."""
    reg = g[y0:y1, X0:X1]
    cols = np.where((reg > 215).mean(0) < 0.5)[0]; rows = np.where((reg > 215).mean(1) < 0.5)[0]
    return im[y0 + rows.min():y0 + rows.max() + 1, X0 + cols.min():X0 + cols.max() + 1]


A1 = panel(507, 756); A2 = panel(1000, 1261)        # D0 aPD-L1, D14 aPD-L1
h = min(A1.shape[0], A2.shape[0]); w = min(A1.shape[1], A2.shape[1]); A1, A2 = A1[4:h - 4, 4:w - 6], A2[4:h - 4, 4:w - 6]      # shave the gutter remnants
Z = 3.0; up = lambda a: cv2.resize(a, None, fx=Z, fy=Z, interpolation=cv2.INTER_CUBIC)
P = [up(A1), up(A2)]; H = max(p.shape[0] for p in P)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
gap = 50; top = 110; W = sum(p.shape[1] for p in P) + gap * 3
cv = Image.new("RGB", (W, top + H + 30), "white"); d = ImageDraw.Draw(cv); x = gap
for p, name in zip(P, ("Time point 1", "Time point 2")):
    cv.paste(Image.fromarray(cv2.cvtColor(p, cv2.COLOR_BGR2RGB)), (x, top))
    tw = d.textlength(name, font=font); d.text((x + (p.shape[1] - tw) / 2, 30), name, font=font, fill="black"); x += p.shape[1] + gap
cv.save(out / "mouse_reuse_two_time_points_anonymized.png"); print(cv.size, A1.shape, A2.shape)

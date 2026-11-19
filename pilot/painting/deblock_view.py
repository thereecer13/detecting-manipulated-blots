"""Contrast views of a blot with the 8 px JPEG grid removed.
  python3 deblock_view.py in.png out.png
Deblocking: re-compress the image at 16 pixel offsets and average (structure locked to the 8 px grid cancels)."""
import sys, cv2, numpy as np
sys.path.insert(0, __file__.rsplit('/', 2)[0])
from views import levels_richardson
def deblock(g, q=70):
    acc = np.zeros(g.shape, np.float64); n = 0
    for dy in range(0, 8, 2):
        for dx in range(0, 8, 2):
            s = np.roll(np.roll(g, dy, 0), dx, 1); _, b = cv2.imencode('.jpg', s, [cv2.IMWRITE_JPEG_QUALITY, q])
            acc += np.roll(np.roll(cv2.imdecode(b, 0), -dy, 0), -dx, 1); n += 1
    return np.clip(np.round(acc / n), 0, 255).astype(np.uint8)
def lab(x, t):
    x = cv2.resize(x, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC); o = np.full((x.shape[0] + 30, x.shape[1]), 255, np.uint8)
    o[30:] = x; cv2.putText(o, t, (4, 21), 0, 0.6, 0, 2, cv2.LINE_AA); return o
if __name__ == '__main__':
    g = cv2.imread(sys.argv[1], 0); d = deblock(g)
    cv2.imwrite(sys.argv[2], np.hstack([lab(g, 'original'), lab(levels_richardson(g), '8.5x as before'),
        lab(levels_richardson(d), '8.5x, JPEG grid removed'), lab(levels_richardson(d, width=75), '3.4x, JPEG grid removed')]))

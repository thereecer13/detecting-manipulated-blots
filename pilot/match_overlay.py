"""Visual check of a background match between two blot figures.

The second image (B) is aligned to the first (A) by scale and shift so that their background noise
lines up best (noise residuals with bands and page masked, normalized cross-correlation over shifts,
scales around the ratio of the two blot panels' widths). The comparison is done at the smaller image's resolution (the larger one is
shrunk) so fine noise is never smoothed by upscaling. Then:
  - a GIF flips between A and the aligned B (both equalized inside the blot), cropped to the
    area the two share, so a reused background stays still while bands change;
  - a match map: local correlation of the two noise residuals in windows of about 1/25 of the
    panel width; windows above --local (default 0.5) are shaded orange and outlined, on A and,
    mapped back, on B, shown side by side.

    python pilot/match_overlay.py A.jpg B.jpg out_prefix --label-a "PA5-99275" --label-b "PA5-102533 (B)"
"""
import argparse, sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(Path(__file__).parent))
from find_shared_backgrounds import panels
from views import equalized, blot_mask
import template_match as tm
Image.MAX_IMAGE_PIXELS = None
ORANGE = (255, 140, 0)


def gray(img):
    return np.asarray(img.convert("L")).astype(np.float32)


def residual(g):
    """Fine noise residual with page and bands set to 0. Bands are pixels much darker than their
    local surroundings (not a global percentile, which would drop a whole dark membrane)."""
    r = g - cv2.GaussianBlur(g, (0, 0), 1.2)
    page = cv2.dilate((g >= 236).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    k = max(15, (min(g.shape) // 8) | 1)
    local = cv2.medianBlur(np.clip(g, 0, 255).astype(np.uint8), min(k, 255) if min(k, 255) % 2 else min(k, 255) - 1).astype(np.float32)
    band = cv2.dilate((g < local - 25).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    valid = ~page & ~band
    return np.where(valid, r, 0).astype(np.float32), valid


def shrink(ga, s):
    wt = max(8, round(ga.shape[1] / s)); ht = max(8, round(ga.shape[0] * wt / ga.shape[1]))
    return cv2.resize(ga, (wt, ht), interpolation=cv2.INTER_AREA if s > 1 else cv2.INTER_LINEAR)


def panel_width(g):
    return max(panels(g.astype(np.uint8)), key=lambda b: b[2] * b[3])[2]


def _panel_map(g):
    """template_match.noise_map with its crop geometry: (map, x0, y0, k) where map pixel (u, v) is
    image pixel (x0 + k*u, y0 + k*v)."""
    gi = g.astype(np.uint8)
    x, y, w, h = max(panels(gi), key=lambda b: b[2] * b[3])
    dx, dy = round(0.05 * w), round(0.05 * h)
    m = tm.noise_map(Image.fromarray(gi))
    if m is None: return None
    return m, x + dx, y + dy, (w - 2 * dx) / tm.W


def _coarse(ga, gb):
    """Detector-level alignment on panel noise maps. Returns (score, s, dx, dy) mapping B pixel (X, Y)
    to A pixel (s*X + dx, s*Y + dy)."""
    A, B = _panel_map(ga), _panel_map(gb)
    if A is None or B is None: return None
    best = None
    for (P, Q, flip) in ((A, B, False), (B, A, True)):     # template from P searched in Q
        pm, qm = P[0], Q[0]
        h, w = pm.shape; ty, tx = round(0.1 * h), round(0.1 * w); t = pm[ty:h - ty, tx:w - tx]
        if not t.any(): continue
        for sc in tm.SCALES:
            qq = cv2.resize(qm, (max(8, round(qm.shape[1] * sc)), max(8, round(qm.shape[0] * sc))), interpolation=cv2.INTER_LINEAR)
            py, px = round(0.15 * qq.shape[0]), round(0.15 * qq.shape[1])
            qq = cv2.copyMakeBorder(qq, py, py, px, px, cv2.BORDER_CONSTANT, value=0)
            if qq.shape[0] < t.shape[0] or qq.shape[1] < t.shape[1]: continue
            _, mx, _, (x, y) = cv2.minMaxLoc(cv2.matchTemplate(qq, t, cv2.TM_CCORR_NORMED))
            if best is None or mx > best[0]:
                # P-map (u, v) <-> Q-map ((u - tx + x - px) / sc, (v - ty + y - py) / sc)
                # P image = P.x0 + kP*u ; Q image = Q.x0 + kQ*qmap  =>  P = aP*Q + bP
                kP, kQ = P[3], Q[3]
                aP = kP * sc / kQ
                bx = P[1] + kP * (tx - x + px) - aP * Q[1]
                by = P[2] + kP * (ty - y + py) - aP * Q[2]
                if not flip: best = (float(mx), aP, bx, by)                      # A = aP*B + b
                else: best = (float(mx), 1 / aP, -bx / aP, -by / aP)            # P is B: invert
    return best


def align(ga, gb):
    """(score, s, dx, dy): B pixel (X, Y) maps to A pixel (s*X + dx, s*Y + dy). Start from the whole
    figures at their size ratio and from the detector's panel-level alignment, then refine scale (+-3%) and shift (+-3 B pixels) by the direct
    correlation of the fine noise at B's resolution."""
    starts = [(ga.shape[1] / gb.shape[1], 0.0, 0.0)]          # whole figures at their size ratio
    c = _coarse(ga, gb)                                        # detector's panel-level alignment
    if c is not None: starts.append(c[1:])
    best = (-1, starts[0][0], 0.0, 0.0)
    # A is shrunk to whole-pixel widths around ga.w / s0 (each width is one scale), and B is placed at
    # whole-pixel offsets: fine noise only correlates at exact pixel alignment
    for s0, dx0, dy0 in starts:
        w0 = ga.shape[1] / s0
        for wt in range(max(16, int(w0 * 0.97)), int(w0 * 1.03) + 2):
            s = ga.shape[1] / wt
            bx, by = round(dx0 / s), round(dy0 / s)
            for oy in range(-3, 4):
                for ox in range(-3, 4):
                    dx, dy = (bx + ox) * s, (by + oy) * s
                    r = global_corr(ga, gb, s, dx, dy)
                    if r > best[0]: best = (r, float(s), float(dx), float(dy))
    return best


def global_corr(ga, gb, s, dx, dy):
    gas = shrink(ga, s)
    M = np.float32([[1, 0, dx / s], [0, 1, dy / s]])
    gbw = cv2.warpAffine(gb, M, (gas.shape[1], gas.shape[0]), flags=cv2.INTER_NEAREST, borderValue=255)
    inside = cv2.warpAffine(np.ones_like(gb), M, (gas.shape[1], gas.shape[0]), flags=cv2.INTER_NEAREST, borderValue=0) > 0
    ra, va = residual(gas); rb, vb = residual(gbw); v = va & vb & inside
    if v.sum() < 300: return -1
    x, y = ra[v], rb[v]
    return float(np.corrcoef(x, y)[0, 1]) if x.std() > 1e-6 and y.std() > 1e-6 else -1


def local_match(ga, gb, s, dx, dy, win):
    """Local correlation of the two noise residuals, at B's resolution (A shrunk by 1/s, B shifted).
    Returns the match mask and valid mask in that frame, plus the frame's shape."""
    gas = shrink(ga, s)
    M = np.float32([[1, 0, dx / s], [0, 1, dy / s]])
    gbw = cv2.warpAffine(gb, M, (gas.shape[1], gas.shape[0]), flags=cv2.INTER_NEAREST, borderValue=255)
    inside = cv2.warpAffine(np.ones_like(gb), M, (gas.shape[1], gas.shape[0]), flags=cv2.INTER_NEAREST, borderValue=0) > 0
    ra, va = residual(gas); rb, vb = residual(gbw)
    v = va & vb & inside & blot_mask(gas.astype(np.uint8)) & blot_mask(np.clip(gbw, 0, 255).astype(np.uint8))   # blot panels only: no ladder text
    ra, rb = np.where(v, ra, 0), np.where(v, rb, 0)
    k = (win, win)
    num = cv2.blur(ra * rb, k); den = np.sqrt(cv2.blur(ra * ra, k) * cv2.blur(rb * rb, k))
    cover = cv2.blur(v.astype(np.float32), k)
    lc = np.where((den > 1e-6) & (cover > 0.4), num / np.maximum(den, 1e-6), 0)
    return lc, v, inside, gbw


def shade(img_gray, mask, label, font):
    rgb = Image.fromarray(img_gray.astype(np.uint8)).convert("RGB")
    over = np.asarray(rgb).astype(np.float32).copy()
    over[mask] = 0.6 * over[mask] + 0.4 * np.array(ORANGE)
    out = Image.fromarray(over.astype(np.uint8))
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    d = ImageDraw.Draw(out)
    for c in cs:
        pts = [tuple(p[0]) for p in c]
        if len(pts) > 2: d.line(pts + [pts[0]], fill=ORANGE, width=2)
    canvas = Image.new("RGB", (out.size[0], out.size[1] + 26), "white"); canvas.paste(out, (0, 26))
    ImageDraw.Draw(canvas).text((4, 4), label, fill=(0, 0, 0), font=font)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path); ap.add_argument("b", type=Path); ap.add_argument("out", type=Path)
    ap.add_argument("--label-a", default="A"); ap.add_argument("--label-b", default="B")
    ap.add_argument("--local", type=float, default=0.5)
    ap.add_argument("--json", type=Path, help="append a summary line here")
    a = ap.parse_args()
    try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception: font = ImageFont.load_default()
    ga, gb = gray(Image.open(a.a)), gray(Image.open(a.b))
    score, s, dx, dy = align(ga, gb)
    win = max(7, round(panel_width(gb) / 25)) | 1
    lc, v, inside, gbw = local_match(ga, gb, s, dx, dy, win)
    m = (lc > a.local) & v
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((win // 2 | 1,) * 2, np.uint8)) > 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    m = np.isin(lab, [i for i in range(1, n) if st[i][4] >= win * win])
    share = float(m.sum() / max(v.sum(), 1))
    # GIF: equalized, in the shrunk-A frame, cropped to the shared area
    gas = cv2.resize(ga, (m.shape[1], m.shape[0]), interpolation=cv2.INTER_AREA)
    ys, xs = np.where(inside)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    ea = equalized(gas.astype(np.uint8)); eb = equalized(np.clip(gbw, 0, 255).astype(np.uint8))
    fa, fb = Image.fromarray(ea[y0:y1, x0:x1]), Image.fromarray(eb[y0:y1, x0:x1])
    z = 460 / max(fa.size[1], 1)
    fa = fa.resize((round(fa.size[0] * z), round(fa.size[1] * z)), Image.NEAREST); fb = fb.resize(fa.size, Image.NEAREST)
    frames = []
    for f, lbl in ((fa, a.label_a), (fb, a.label_b + " (aligned)")):
        c = Image.new("L", (f.size[0], f.size[1] + 24), 255); c.paste(f, (0, 24)); ImageDraw.Draw(c).text((4, 4), lbl, fill=0, font=font); frames.append(c.convert("P"))
    frames[0].save(str(a.out) + "_flip.gif", save_all=True, append_images=frames[1:], duration=700, loop=0)
    # masks back to each image's own frame: A = upscale by s; B = undo the shift
    m_a = cv2.resize(m.astype(np.uint8), (ga.shape[1], ga.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    mb = cv2.warpAffine(m.astype(np.uint8), np.float32([[1, 0, -dx / s], [0, 1, -dy / s]]), (gb.shape[1], gb.shape[0]), flags=cv2.INTER_NEAREST) > 0
    m = m_a
    # match map on both images (B: map the mask back to B's own frame)
    pa = shade(equalized(ga.astype(np.uint8)), m, f"{a.label_a}: matching background shaded", font)
    pb = shade(equalized(gb.astype(np.uint8)), mb, f"{a.label_b}: same areas", font)
    h = max(pa.size[1], pb.size[1]); pb = pb.resize((round(pb.size[0] * pa.size[1] / pb.size[1]), pa.size[1]))
    sheet = Image.new("RGB", (pa.size[0] + pb.size[0] + 16, pa.size[1] + 24), "white")
    sheet.paste(pa, (0, 0)); sheet.paste(pb, (pa.size[0] + 16, 0))
    ImageDraw.Draw(sheet).text((4, pa.size[1] + 4), f"noise correlation over shared background {score:.2f}; matching windows cover {share:.0%} of the shared background (local corr > {a.local})", fill=(0, 0, 0), font=font)
    sheet.save(str(a.out) + "_match.png")
    if a.json:
        with open(a.json, "a") as f: f.write(__import__("json").dumps({"a": a.label_a, "b": a.label_b, "score": score, "scale": s, "dx": dx, "dy": dy, "match_share": share}) + "\n")
    print(f"{a.label_a} vs {a.label_b}: alignment {score:.2f}, scale {s:.2f}, match share {share:.0%}")


if __name__ == "__main__":
    main()

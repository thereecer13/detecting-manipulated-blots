"""Measurements that implement the expert rules (rulebook v1) for one blot image.

Rule 1, duplicated bands: outline shapes of every band are compared with every other band in
the image; outline similarity >= 0.95 is suspicious, more so when several pairs match.
Rule 2, splices: continuous, straight runs of sharp brightness change outside bands.
Rule 3, painting: after raising contrast (Richardson's method), blotchy flat patches that
stand out against an otherwise textured, smooth background.

Everything is computed on the native-resolution grayscale image.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

SIM_THRESHOLD = 0.95


def gray(img):
    return np.asarray(img.convert("L"))


# ---------- rule 1: bands and outline similarity ----------

def _split_wide(mask, comp_box, dark):
    """Split a component spanning several lanes at minima of its column darkness profile."""
    x, y, w, h = comp_box
    sub = mask[y:y + h, x:x + w]
    prof = (sub * dark[y:y + h, x:x + w]).sum(0).astype(float)
    if w < 6 or prof.max() <= 0:
        return [comp_box]
    k = max(3, w // 40) | 1
    prof = np.convolve(prof, np.ones(k) / k, mode="same")
    cuts = [i for i in range(2, w - 2)
            if prof[i] <= prof[i - 1] and prof[i] <= prof[i + 1] and prof[i] < 0.45 * prof.max()]
    # merge cut candidates that are close together
    merged = []
    for c in cuts:
        if merged and c - merged[-1] < max(4, w // 30):
            continue
        merged.append(c)
    edges = [0] + merged + [w]
    boxes = []
    for a, b in zip(edges[:-1], edges[1:]):
        cols = sub[:, a:b]
        rows = np.where(cols.any(1))[0]
        if b - a >= 3 and len(rows):
            boxes.append((x + a, y + rows[0], b - a, rows[-1] - rows[0] + 1))
    return boxes or [comp_box]


def find_bands(g):
    """Dark blobs on a lighter background, one box per band (wide merged rows are split by lane)."""
    h, w = g.shape
    blur = cv2.GaussianBlur(g, (0, 0), 1.0)
    dark = 255 - blur
    # remove slow background shading so gradients are not taken as bands
    k = max(15, (min(h, w) // 2) | 1)
    bg = cv2.morphologyEx(dark, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    top = cv2.subtract(dark, bg)
    if top.max() < 10:
        return [], np.zeros_like(g, bool)
    t, _ = cv2.threshold(top, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = (top > max(t, 12)).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    min_area = max(20, 0.0015 * h * w)
    boxes = []
    keep = np.zeros_like(mask)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < min_area:
            continue
        fill = area / (bw * bh)
        if fill < 0.15:          # hollow outlines: panel frames, borders
            continue
        if bh > 0.9 * h and bw < 0.05 * w:   # vertical rules / separators
            continue
        comp = (lab == i).astype(np.uint8)
        keep |= comp
        med_w = None
        boxes.append((x, y, bw, bh, comp))
    if not boxes:
        return [], keep.astype(bool)
    med_w = np.median([b[2] for b in boxes])
    out = []
    for x, y, bw, bh, comp in boxes:
        parts = _split_wide(comp, (x, y, bw, bh), dark.astype(np.float32) / 255) if bw > 1.8 * med_w and bw > 0.15 * w else [(x, y, bw, bh)]
        for (px, py, pw, ph) in parts:
            m = comp[py:py + ph, px:px + pw].astype(bool)
            if m.sum() >= min_area * 0.5:
                out.append({"box": (int(px), int(py), int(pw), int(ph)), "mask": m})
    return out, keep.astype(bool)


TRANSFORMS = {"as is": lambda a: a, "flipped left-right": lambda a: a[:, ::-1],
              "flipped up-down": lambda a: a[::-1, :], "rotated 180": lambda a: a[::-1, ::-1]}


def _on_canvas(m, H, W):
    c = np.zeros((H, W), bool)
    y0, x0 = (H - m.shape[0]) // 2, (W - m.shape[1]) // 2
    c[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
    return c


def outline_similarity(a, b):
    """Dice overlap of two band outlines, centred on each other; best over flips and 180 rotation."""
    if not (0.7 <= a.sum() / max(b.sum(), 1) <= 1.43):
        return 0.0, "as is"
    H, W = max(a.shape[0], b.shape[0]), max(a.shape[1], b.shape[1])
    ca = _on_canvas(a, H, W)
    best = (0.0, "as is")
    for name, f in TRANSFORMS.items():
        cb = _on_canvas(f(b), H, W)
        best_shift = 0.0
        for dy in (-1, 0, 1):          # allow one-pixel misalignment from rounding
            for dx in (-1, 0, 1):
                s = np.roll(np.roll(cb, dy, 0), dx, 1)
                d = 2 * (ca & s).sum() / (ca.sum() + s.sum())
                best_shift = max(best_shift, d)
        if best_shift > best[0]:
            best = (best_shift, name)
    return float(best[0]), best[1]


def texture_similarity(ga, gb, how):
    """Correlation of the two band crops' gray values (after the same flip), resized to match."""
    gb = TRANSFORMS[how](gb)
    gb = cv2.resize(gb.astype(np.float32), (ga.shape[1], ga.shape[0]), interpolation=cv2.INTER_AREA)
    a = ga.astype(np.float32).ravel(); b = gb.ravel()
    if a.std() < 1e-3 or b.std() < 1e-3:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def band_pairs(g, bands):
    out = []
    for i in range(len(bands)):
        for j in range(i + 1, len(bands)):
            a, b = bands[i], bands[j]
            s, how = outline_similarity(a["mask"], b["mask"])
            if s >= 0.85:
                xa, ya, wa, ha = a["box"]; xb, yb, wb, hb = b["box"]
                t = texture_similarity(g[ya:ya + ha, xa:xa + wa], g[yb:yb + hb, xb:xb + wb], how)
                out.append({"i": i, "j": j, "outline": s, "texture": t, "transform": how,
                            "small": int(min(a["mask"].sum(), b["mask"].sum()) < 150)})
    return sorted(out, key=lambda p: -p["outline"])


# ---------- rule 2: straight transitions outside bands ----------

def noise_sigma(g):
    f = g.astype(np.float32)
    r = f - cv2.GaussianBlur(f, (0, 0), 1.5)
    return float(max(np.median(np.abs(r - np.median(r))) * 1.4826, 0.5))


def straight_transitions(g, band_mask, bands=(), min_frac=0.4):
    """Columns/rows along which brightness steps sharply, consistently, over a long straight run,
    ignoring pixels on or next to bands. Lines within 4% of the image border (figure frames, crop
    edges) are skipped. Each line is classed as an "edge" (different brightness on the two sides)
    or a "thin stripe" (a narrow bright/dark line with the same brightness on both sides)."""
    f = cv2.GaussianBlur(g.astype(np.float32), (0, 0), 0.8)
    sig = noise_sigma(g)
    H0, W0 = g.shape
    raw = g.astype(np.float32)
    resid = raw - cv2.GaussianBlur(raw, (0, 0), 1.5)
    near_band = cv2.dilate(band_mask.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    # rows of bands: also skip a margin above and below each band (smears and faint band edges)
    row_band = near_band.copy()
    for b in bands:
        x, y, bw, bh = b["box"]; m = max(3, bh // 2)
        row_band[max(0, y - m):y + bh + m, x:x + bw] = True
    lines = []
    for axis in ("vertical", "horizontal"):
        img = f if axis == "vertical" else f.T
        res = resid if axis == "vertical" else resid.T
        nb = near_band if axis == "vertical" else row_band.T
        H, W = img.shape
        if W < 12 or H < 12:
            continue
        margin = max(4, int(0.04 * W))
        for x in range(margin, W - margin):
            step = img[:, x + 1:x + 3].mean(1) - img[:, x - 2:x].mean(1)
            valid = ~(nb[:, x - 2:x + 3].any(1))
            if valid.sum() < 0.3 * H:
                continue
            thr = max(2.5 * sig, 3.0)
            for sign in (1, -1):
                strong = (sign * step > thr) & valid
                best, run, run_vals, best_vals, rows, best_rows = 0, 0, [], [], [], []
                for y in range(H):
                    if not valid[y]:
                        continue
                    if strong[y]:
                        run += 1; run_vals.append(sign * step[y]); rows.append(y)
                    else:
                        if run > best: best, best_vals, best_rows = run, run_vals, rows
                        run, run_vals, rows = 0, [], []
                if run > best: best, best_vals, best_rows = run, run_vals, rows
                frac = best / max(valid.sum(), 1)
                if frac >= min_frac and best >= 12:
                    r = np.array(best_rows)
                    lo = max(0, x - 8); hi = min(W, x + 9)
                    left = img[r, lo:max(lo + 1, x - 3)].mean(); right = img[r, min(hi - 1, x + 4):hi].mean()
                    kind = "edge" if abs(right - left) >= np.median(best_vals) / 3 else "thin stripe"
                    # is one side blank (no grain at all, near pure white/black)? then it is the blot's
                    # boundary against empty figure area or a drawn frame, not a transition inside the blot
                    sides = []
                    for a0, a1 in ((max(0, x - 10), max(1, x - 3)), (min(W - 1, x + 4), min(W, x + 11))):
                        sd = float(res[r, a0:a1].std()); mu = float(img[r, a0:a1].mean())
                        sides.append(sd < max(0.3 * sig, 0.4) and (mu > 245 or mu < 10))
                    if kind == "edge" and any(sides):
                        kind = "blot boundary against blank figure area"
                    lines.append({"axis": axis, "pos": x / W, "pos_px": x, "frac": frac, "kind": kind,
                                  "step": float(np.median(best_vals)), "step_sigma": float(np.median(best_vals) / sig),
                                  "direction": "brighter" if sign > 0 else "darker"})
    lines.sort(key=lambda l: (l["axis"], l["pos_px"]))
    merged = []
    for l in lines:
        if merged and merged[-1]["axis"] == l["axis"] and l["pos_px"] - merged[-1]["pos_px"] <= 3:
            if l["frac"] > merged[-1]["frac"]: merged[-1] = l
            continue
        merged.append(l)
    return sorted(merged, key=lambda l: -l["frac"]), sig


# ---------- rule 3: flat patches after raising contrast ----------

def flat_patches(g, band_mask):
    f = g.astype(np.float32)
    r = f - cv2.GaussianBlur(f, (0, 0), 1.5)
    local_sd = np.sqrt(np.maximum(cv2.blur(r * r, (7, 7)), 0))
    bg = ~cv2.dilate(band_mask.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    bg[:3, :] = bg[-3:, :] = False; bg[:, :3] = bg[:, -3:] = False
    if bg.sum() < 100:
        return {"assessable": False, "reason": "almost no background outside bands", "patches": []}
    ref = float(np.median(local_sd[bg]))
    textured_frac = float((local_sd[bg] > 0.5).mean())
    if ref < 0.5:
        return {"assessable": False, "reason": "the whole background is flat (no grain anywhere), so flat patches cannot stand out",
                "patches": [], "textured_frac": textured_frac}
    flat = (local_sd < 0.2 * ref) & bg
    flat = cv2.morphologyEx(flat.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(flat, 8)
    h, w = g.shape
    patches = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area >= max(40, 0.004 * h * w):
            m = lab == i
            patches.append({"box": (int(x), int(y), int(bw), int(bh)), "area_frac": float(area / (h * w)),
                            "mean_gray": float(f[m].mean()), "mask": m})
    patches.sort(key=lambda p: -p["area_frac"])
    return {"assessable": True, "noise_ref": ref, "textured_frac": textured_frac, "patches": patches}


# ---------- run everything for one image ----------

def analyse(img):
    g = gray(img)
    bands, band_mask = find_bands(g)
    pairs = band_pairs(g, bands)
    lines, sig = straight_transitions(g, band_mask, bands)
    flat = flat_patches(g, band_mask)
    return {"g": g, "bands": bands, "pairs": pairs, "lines": lines, "noise": sig, "flat": flat}


def summary_text(a):
    h, w = a["g"].shape
    L = []
    L.append(f"Image analysed at native resolution {w}x{h} px. Background noise level (robust SD): {a['noise']:.1f} gray levels.")
    nb = len(a["bands"])
    L.append(f"RULE 1 (duplicated bands): {nb} band(s) detected (numbered on the overlay, left to right then top to bottom).")
    hits = [p for p in a["pairs"] if p["outline"] >= SIM_THRESHOLD]
    if nb < 2:
        L.append("  Fewer than two bands found, so no comparison was possible.")
    elif not hits:
        top = a["pairs"][0]["outline"] if a["pairs"] else 0.0
        L.append(f"  No band pair reaches outline similarity {SIM_THRESHOLD}. Highest pair similarity: {top:.2f}.")
    else:
        bands_involved = {p["i"] for p in hits} | {p["j"] for p in hits}
        L.append(f"  {len(hits)} band pair(s) with outline similarity >= {SIM_THRESHOLD}, involving {len(bands_involved)} bands:")
        for p in hits[:8]:
            tex = "n/a" if np.isnan(p["texture"]) else f"{p['texture']:.2f}"
            L.append(f"   - bands {p['i']+1} & {p['j']+1}: outline {p['outline']:.2f} ({p['transform']}), gray-value correlation {tex}"
                     + (" [small bands: outline match is less informative]" if p["small"] else ""))
    L.append("RULE 2 (splices): straight lines outside bands along which brightness changes sharply and consistently.")
    if not a["lines"]:
        L.append("  None found (no straight run covering >= 40% of the line's length outside bands; lines within 4% of the image border are ignored).")
    for l in a["lines"][:6]:
        where = f"x = {l['pos']:.2f} of width" if l["axis"] == "vertical" else f"y = {l['pos']:.2f} of height"
        L.append(f"   - {l['axis']} {l['kind']} at {where}: continuous over {l['frac']*100:.0f}% of its length outside bands, "
                 f"steps {l['direction']} by {l['step']:.1f} gray levels ({l['step_sigma']:.1f}x noise)")
    fl = a["flat"]
    L.append("RULE 3 (painting): flat, grain-free patches standing out against otherwise textured background (contrast raised).")
    if not fl["assessable"]:
        L.append(f"  Not assessable: {fl['reason']}.")
    elif not fl["patches"]:
        L.append(f"  None found. {fl['textured_frac']*100:.0f}% of the background shows grain.")
    else:
        tot = sum(p["area_frac"] for p in fl["patches"])
        L.append(f"  {len(fl['patches'])} flat patch(es) covering {tot*100:.1f}% of the image, while {fl['textured_frac']*100:.0f}% of the background shows grain:")
        for p in fl["patches"][:6]:
            x, y, bw, bh = p["box"]
            L.append(f"   - patch at x {x/w:.2f}-{(x+bw)/w:.2f}, y {y/h:.2f}-{(y+bh)/h:.2f}: {p['area_frac']*100:.1f}% of image, mean gray {p['mean_gray']:.0f}")
    return "\n".join(L)


def overlay(a, eq, long_side=512):
    """Draw the measurements on the equalized view: bands (green, red if in a >= 0.95 pair),
    straight transitions (blue), flat patches (magenta)."""
    h, w = a["g"].shape
    s = long_side / max(h, w)
    base = np.asarray(eq.convert("L"))
    rgb = np.stack([base] * 3, -1).astype(np.float32)
    for p in a["flat"].get("patches", []):
        m = p["mask"]
        rgb[m] = rgb[m] * 0.4 + np.array([255, 0, 255]) * 0.6
    im = Image.fromarray(rgb.astype(np.uint8)).resize((max(1, round(w * s)), max(1, round(h * s))), Image.NEAREST)
    d = ImageDraw.Draw(im)
    hot = {p["i"] for p in a["pairs"] if p["outline"] >= SIM_THRESHOLD} | {p["j"] for p in a["pairs"] if p["outline"] >= SIM_THRESHOLD}
    for k, b in enumerate(a["bands"]):
        x, y, bw, bh = b["box"]
        d.rectangle([x * s, y * s, (x + bw) * s, (y + bh) * s], outline=(255, 0, 0) if k in hot else (0, 200, 0), width=2)
        d.text((x * s + 2, y * s + 1), str(k + 1), fill=(255, 0, 0) if k in hot else (0, 160, 0))
    for l in a["lines"][:6]:
        if l["axis"] == "vertical":
            X = l["pos_px"] * s; d.line([X, 0, X, h * s], fill=(0, 90, 255), width=2)
        else:
            Y = l["pos_px"] * s; d.line([0, Y, w * s, Y], fill=(0, 90, 255), width=2)
    return im


def rule_flags(a):
    """The rules applied mechanically, no judgment: which rules fire."""
    hits = [p for p in a["pairs"] if p["outline"] >= SIM_THRESHOLD]
    return {"dup_pairs": len(hits), "lines": sum(l["kind"] == "edge" for l in a["lines"]), "stripes": sum(l["kind"] == "thin stripe" for l in a["lines"]),
            "boundaries": sum(l["kind"].startswith("blot boundary") for l in a["lines"]),
            "flat_patches": len(a["flat"].get("patches", []))}

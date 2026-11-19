"""Remnant-shape features for painted backgrounds (reviewer's description: painting is imperfect and leaves
irregular textured remnants outside the bands; a uniformly flat background cannot be called).

Works on 8x8 JPEG blocks inside the blot panels. A block is 'flat' if its grey range is <= 1, 'band' if it
is clearly darker than the background, otherwise 'textured'. Features describe how the textured background
blocks are arranged among the flat ones.
  python3 feat_v3.py image.png            -> prints the features
"""
import sys, json
import numpy as np, cv2
sys.path.insert(0, __file__.rsplit('/', 2)[0])
from views import blot_mask_v2

def features(g):
    m = blot_mask_v2(g); H, W = g.shape; h8, w8 = H // 8, W // 8
    if h8 < 6 or w8 < 6: return None
    B = g[:h8 * 8, :w8 * 8].reshape(h8, 8, w8, 8).swapaxes(1, 2).reshape(h8, w8, 64).astype(np.int16)
    inb = m[:h8 * 8, :w8 * 8].reshape(h8, 8, w8, 8).swapaxes(1, 2).reshape(h8, w8, 64).all(2)
    if inb.sum() < 60: return None
    rng = B.max(2) - B.min(2); mean = B.mean(2)
    bg_lvl = np.median(mean[inb]); dark = inb & (mean < bg_lvl - 12)
    band = cv2.dilate(dark.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0     # bands and their halo
    bg = inb & ~band
    if bg.sum() < 40: return None
    flat = bg & (rng <= 1); tex = bg & (rng > 1)
    f = {"bg_blocks": int(bg.sum()), "flat_share": float(flat.sum() / bg.sum())}
    # textured remnants: connected groups of textured background blocks
    n, lab, st, _ = cv2.connectedComponentsWithStats(tex.astype(np.uint8), 8)
    sizes = st[1:, cv2.CC_STAT_AREA] if n > 1 else np.array([])
    f["n_islands"] = int(len(sizes)); f["island_max"] = int(sizes.max()) if len(sizes) else 0
    f["island_mid"] = int(((sizes >= 3) & (sizes <= 60)).sum())               # remnant-sized groups
    f["single_share"] = float((sizes == 1).sum() / max(tex.sum(), 1))          # isolated blocks = compression speckle
    # clumping: chance that a 4-neighbour of a textured block is textured, relative to the textured share
    t = tex.astype(np.float32); nb = cv2.filter2D(t, -1, np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], np.float32), borderType=cv2.BORDER_CONSTANT)
    bn = cv2.filter2D(bg.astype(np.float32), -1, np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], np.float32), borderType=cv2.BORDER_CONSTANT)
    p_t = tex.sum() / bg.sum(); f["clump"] = float((nb[tex].sum() / max(bn[tex].sum(), 1)) - p_t) if tex.any() else 0.0
    # how strong is the texture inside the remnants, and how sharply does it stop at the flat area
    f["tex_range"] = float(np.median(rng[tex])) if tex.any() else 0.0
    edge_flat = flat & (cv2.dilate(tex.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    edge_tex = tex & (cv2.dilate(flat.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    f["edge_step"] = float(np.median(rng[edge_tex])) if edge_tex.any() else 0.0  # range of textured blocks touching flat
    # paint colour: flat blocks of one grey level vs flat blocks following the membrane's shading
    if flat.any():
        lv = np.round(mean[flat]).astype(int); c = np.bincount(lv - lv.min())
        f["flat_levels"] = int((c > 0).sum()); f["flat_top_share"] = float(c.max() / c.sum())
        f["lvl_step"] = float(abs(np.median(mean[tex]) - np.median(mean[flat]))) if tex.any() else 0.0
    else: f["flat_levels"] = 0; f["flat_top_share"] = 0.0; f["lvl_step"] = 0.0
    # largest flat region as a share of the background (paint is one big region with holes)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(flat.astype(np.uint8), 4)
    f["flat_big"] = float(st2[1:, cv2.CC_STAT_AREA].max() / bg.sum()) if n2 > 1 else 0.0
    # v3b: one-colour "paint" next to real grain. paint = flat blocks at the most common flat level (+-1);
    # grain = background blocks with range >= 3, split by distance from the bands
    if flat.any():
        lv = np.round(mean).astype(int); top = np.bincount(lv[flat]).argmax()
        paint = flat & (np.abs(lv - top) <= 1)
    else: paint = flat
    grain = bg & (rng >= 3)
    far = ~(cv2.dilate(dark.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0)
    f["paint_share"] = float(paint.sum() / bg.sum())
    f["grain_share"] = float(grain.sum() / bg.sum())
    f["grain_far"] = float((grain & far).sum() / max((bg & far).sum(), 1))
    f["mix"] = float(min(f["paint_share"], 3 * f["grain_share"]))
    f["mix_far"] = float(min(f["paint_share"], 3 * f["grain_far"]))
    # paint touching grain directly: share of paint blocks with a grain 8-neighbour
    f["contact"] = float((paint & (cv2.dilate(grain.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)).sum() / max(paint.sum(), 1))
    return f

if __name__ == '__main__':
    print(json.dumps(features(cv2.imread(sys.argv[1], 0)), indent=1))

"""Screen scraped 'clean' vendor blots before they are used as negatives.

1. Exact duplicates: a scraped image whose 256-bit difference hash is within 2 bits of any Richardson
   original (any problem type), or of an earlier scraped image, is dropped. Looser duplicate tests do
   not work on vendor blots: unrelated images share printed ladder labels and layouts, so hashes and
   noise correlations of whole images collide (checked on Richardson images; see the README).
2. Background templates: Richardson's 'background pattern A-H' images reuse the same background
   noise under different bands. Each scraped image's noise residual (darkest 35% masked, which
   removes bands and printed labels) is correlated with up to 5 examples of each template, resized to
   the same shape when the aspect ratios are within 10%. Correlation >= 0.3 with any example drops
   the image. Checked on held-out Richardson images: flags 73% of template images, 0 of 40 others.

    python pilot/screen_scraped.py --scraped scraped --richardson raw/rich_aug
"""
import argparse, csv, io, json, re, zipfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None


def gray(im, width=256):
    g = np.asarray(im.convert("L")).astype(np.float32)
    h = max(8, round(g.shape[0] * width / g.shape[1]))
    return cv2.resize(g, (width, h), interpolation=cv2.INTER_AREA)


def dhash(im):
    g = np.asarray(im.convert("L").resize((17, 16), Image.LANCZOS)).astype(int)
    return int("".join("1" if b else "0" for b in (g[:, 1:] > g[:, :-1]).ravel()), 2)


def hamming(a, b):
    return bin(a ^ b).count("1")


def residual(g):
    r = g - cv2.GaussianBlur(g, (0, 0), 1.5)
    mask = g > np.percentile(g, 35)          # background only: drop the darkest 35% (bands)
    return r, mask


def bg_corr(a, b):
    ra, ma = a; rb, mb = b
    if ra.shape != rb.shape:
        rb = cv2.resize(rb, (ra.shape[1], ra.shape[0])); mb = cv2.resize(mb.astype(np.uint8), (ra.shape[1], ra.shape[0])).astype(bool)
    m = ma & mb
    if m.sum() < 500: return 0.0
    x, y = ra[m], rb[m]
    if x.std() < 1e-3 or y.std() < 1e-3: return 0.0
    return float(np.corrcoef(x, y)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scraped", type=Path, required=True)
    ap.add_argument("--richardson", type=Path, required=True, help="folder with *_catch_all_spreadsheet.csv and *_original_images.zip")
    a = ap.parse_args()
    sheet = next(a.richardson.glob("*_catch_all_spreadsheet.csv")); zpath = next(a.richardson.glob("*_original_images.zip"))
    rows = list(csv.DictReader(open(sheet, encoding="utf-8")))
    z = zipfile.ZipFile(zpath); names = {Path(n).name: n for n in z.namelist()}
    # Richardson hashes and aspect ratios
    rich = []
    for r in rows:
        n = names.get(r["original_image_filename"])
        if not n: continue
        try:
            im = Image.open(io.BytesIO(z.read(n))); rich.append((dhash(im), im.size[1] / im.size[0], n))
        except Exception: pass
    print(f"hashed {len(rich)} Richardson originals")
    # template exemplars
    tmpl = {}
    for r in rows:
        m = re.search(r"pattern ([A-Z])", r["summary"]); n = names.get(r["original_image_filename"])
        if m and n and len(tmpl.setdefault(m.group(1), [])) < 5:
            g = gray(Image.open(io.BytesIO(z.read(n)))); tmpl[m.group(1)].append((g.shape[0] / g.shape[1], residual(g)))
    recs = [json.loads(l) for l in (a.scraped / "scraped.jsonl").read_text().splitlines()]
    kept, seen = [], []
    for rec in recs:
        im = Image.open(a.scraped / "images" / rec["file"]); h = dhash(im)
        g = gray(im); ar = g.shape[0] / g.shape[1]; res = residual(g)
        d_rich = min([hamming(hh, h) for hh, _, _ in rich] or [256])
        best = max([(bg_corr(res, t), L) for L, ex in tmpl.items() for tar, t in ex if abs(tar / ar - 1) < 0.1] or [(0.0, "-")])
        d_scr = min([hamming(hh, h) for hh in seen] or [256])
        rec.update({"hash_dist_richardson": d_rich, "template_corr": round(best[0], 3), "template": best[1], "hash_dist_scraped": d_scr})
        rec["keep"] = d_rich > 2 and best[0] < 0.3 and d_scr > 2
        seen.append(h); kept.append(rec)
    (a.scraped / "screened.jsonl").write_text("\n".join(json.dumps(r) for r in kept) + "\n")
    n = sum(r["keep"] for r in kept)
    print(f"{n}/{len(kept)} kept | dropped: duplicate of a Richardson image {sum(r['hash_dist_richardson'] <= 2 for r in kept)}, "
          f"template background {sum(r['template_corr'] >= 0.3 for r in kept)}, duplicate within scrape {sum(r['hash_dist_scraped'] <= 2 for r in kept)}")


if __name__ == "__main__":
    main()

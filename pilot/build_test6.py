"""Test 6: fresh real vendor blots, same design as test 5 (copied from build_test5.py).

Differences from test 5: clean images are only the fresh scrape that the user reviewed and marked
clean (a JSON list of catalog numbers passed as the 2nd argument), and Richardson images used in
test 5 are excluded as well.

    python pilot/build_test6.py <scratch dir> <clean_catalogs.json> MA5-=N TA8=N TA5=N RAB0=N

Original test 5 description:
Test 5: real vendor blots. Richardson within-blot manipulations vs scraped clean blots from the same
vendors and catalog prefixes (Thermo Fisher MA5-/PA5-, Abnova RAB0 on thermofisher.com, Origene TA8/TA5).

- Manipulated: August 2026 Richardson images with a within-blot problem (no shared-template or
  cross-image findings), file name marked as a western blot ("WB", or Origene's "-w" suffix), not
  used in tests 3-4.
- Clean: scraped images that passed pilot/screen_scraped.py.
- Per catalog prefix, the same number of each, so vendor and prefix carry no signal. The manipulated
  pool is much larger, so each clean image is paired with the unused manipulated image of the same
  prefix that is closest in mean brightness, share of near-white pixels and aspect ratio (after the
  same normalization), so overall brightness and shape carry no signal either.
- Thermo-hosted images (both classes) are scaled to at most 650 px wide, the size of the scraped
  rendition, and every image is re-saved as JPEG quality 85, so size and compression history match.

    python pilot/build_test5.py <scratch dir> <per-class n per prefix: MA5-=20 PA5-=4 RAB0=3 TA8=20 TA5=13>
"""
import csv, hashlib, io, json, random, re, sys, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from views import views
Image.MAX_IMAGE_PIXELS = None
S = Path(sys.argv[1]); CLEAN = set(json.load(open(sys.argv[2]))); targets = {k: int(v) for k, v in (a.split("=") for a in sys.argv[3:])}
ITEMS = S / "test6/items6"; KEY = S / "test6_key"
rng = random.Random(6066)
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
used = set()
for f in ["pilot_key/key.json", "test2_key/key.json", "test3_key/key.json", "test4_key/key.json", "test5_key/key_all204.json"]:
    used |= {k["file"] for k in json.load(open(S / f)) if "file" in k}
rows = list(csv.DictReader(open(S / "raw/rich_aug/260825_catch_all_spreadsheet.csv", encoding="utf-8")))
z = zipfile.ZipFile(S / "raw/rich_aug/260825_original_images.zip"); names = {Path(n).name: n for n in z.namelist()}

def prefix_of(cat, host):
    for p in ["MA5-", "PA5-", "RAB0"]:
        if cat.upper().startswith(p) and "thermofisher.com" in host: return p
    for p in ["TA8", "TA5"]:
        if cat.upper().startswith(p) and "origene.com" in host: return p
    return None

pos = {}
for r in rows:
    p = prefix_of(r["catalog_number"], r["product_link"])
    if (p and not cross.search(r["summary"]) and r["original_image_filename"] in names
            and r["original_image_filename"] not in used and (re.search(r"(^|[-_])WB([-_]|$)", r["original_image_filename"], re.I) or re.search(r"-w\.jpe?g$", r["original_image_filename"], re.I))):
        pos.setdefault(p, []).append(r)
neg = {}
for l in (S / "scraped/screened.jsonl").read_text().splitlines():
    d = json.loads(l)
    if d["keep"] and d["catalog"] in CLEAN: neg.setdefault(d["prefix"], []).append(d)

def normalize(im, thermo):
    im = im.convert("L")
    if thermo and im.size[0] > 650:
        im = im.resize((650, round(im.size[1] * 650 / im.size[0])), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return Image.open(io.BytesIO(buf.getvalue()))

key = []
def emit(img, extra):
    h = hashlib.sha1(f"t6{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / "V_vendor"; d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{h}{suffix}.png")
    key.append({"task": "V_vendor", "id": h, **extra, "size": list(img.size)})

def stats(im):
    g = np.asarray(im.resize((128, max(8, round(im.size[1] * 128 / im.size[0]))))).astype(float)
    return np.array([g.mean() / 255, (g > 245).mean(), np.log(im.size[0] / im.size[1])])

for p, n in targets.items():
    P, N = pos.get(p, []), neg.get(p, [])
    rng.shuffle(P); rng.shuffle(N)
    thermo = p in ("MA5-", "PA5-", "RAB0")
    N = N[:min(n, len(N))]
    if not N or not P: print(f"{p}: nothing to pair"); continue
    pool = P[:max(10 * len(N), 60)]
    pimg = [normalize(Image.open(io.BytesIO(z.read(names[r["original_image_filename"]]))), thermo) for r in pool]
    pst = np.array([stats(im) for im in pimg]); taken = set()
    pairs = 0
    for d in N:
        nim = normalize(Image.open(S / "scraped/images" / d["file"]), thermo); ns = stats(nim)
        order = np.argsort(np.abs(pst - ns).sum(1))
        j = next((int(j) for j in order if int(j) not in taken), None)
        if j is None: break
        taken.add(j); r = pool[j]; pairs += 1
        emit(pimg[j], {"label": 1, "prefix": p, "catalog": r["catalog_number"], "summary": r["summary"], "file": r["original_image_filename"]})
        emit(nim, {"label": 0, "prefix": p, "catalog": d["catalog"], "summary": "", "file": d["file"], "image_url": d["image_url"]})
    print(f"{p}: manipulated pool {len(P)} (searched {len(pool)}), clean {len(N)} -> {pairs} matched pairs")
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
print(Counter((k["prefix"], k["label"]) for k in key))
print("manipulation types:", Counter("painting" if "paint" in k["summary"].lower() else "other" for k in key if k["label"]))

"""Test 5: real vendor blots. Richardson within-blot manipulations vs scraped clean blots from the same
vendors and catalog prefixes (Thermo Fisher MA5-/PA5-, Abnova RAB0 on thermofisher.com, Origene TA8/TA5).

- Manipulated: August 2026 Richardson images with a within-blot problem (no shared-template or
  cross-image findings), file name marked as a western blot ("WB"), not used in tests 3-4.
- Clean: scraped images that passed pilot/screen_scraped.py.
- Per catalog prefix, the same number of each, so vendor and prefix carry no signal.
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
S = Path(sys.argv[1]); targets = {k: int(v) for k, v in (a.split("=") for a in sys.argv[2:])}
ITEMS = S / "test5/items5"; KEY = S / "test5_key"
rng = random.Random(5055)
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
used = set()
for f in ["pilot_key/key.json", "test2_key/key.json", "test3_key/key.json", "test4_key/key.json"]:
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
            and r["original_image_filename"] not in used and re.search(r"(^|[-_])WB([-_]|$)", r["original_image_filename"], re.I)):
        pos.setdefault(p, []).append(r)
neg = {}
for l in (S / "scraped/screened.jsonl").read_text().splitlines():
    d = json.loads(l)
    if d["keep"]: neg.setdefault(d["prefix"], []).append(d)

def normalize(im, thermo):
    im = im.convert("L")
    if thermo and im.size[0] > 650:
        im = im.resize((650, round(im.size[1] * 650 / im.size[0])), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return Image.open(io.BytesIO(buf.getvalue()))

key = []
def emit(img, extra):
    h = hashlib.sha1(f"t5{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / "V_vendor"; d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{h}{suffix}.png")
    key.append({"task": "V_vendor", "id": h, **extra, "size": list(img.size)})

for p, n in targets.items():
    P, N = pos.get(p, []), neg.get(p, [])
    rng.shuffle(P); rng.shuffle(N)
    k = min(n, len(P), len(N))
    print(f"{p}: manipulated available {len(P)}, clean available {len(N)} -> using {k} of each")
    thermo = p in ("MA5-", "PA5-", "RAB0")
    for r in P[:k]:
        emit(normalize(Image.open(io.BytesIO(z.read(names[r["original_image_filename"]]))), thermo),
             {"label": 1, "prefix": p, "catalog": r["catalog_number"], "summary": r["summary"], "file": r["original_image_filename"]})
    for d in N[:k]:
        emit(normalize(Image.open(S / "scraped/images" / d["file"]), thermo),
             {"label": 0, "prefix": p, "catalog": d["catalog"], "summary": "", "file": d["file"], "image_url": d["image_url"]})
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
print(Counter((k["prefix"], k["label"]) for k in key))
print("manipulation types:", Counter("painting" if "paint" in k["summary"].lower() else "other" for k in key if k["label"]))

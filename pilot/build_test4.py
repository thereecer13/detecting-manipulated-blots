"""Fresh blind test set for rulebook v3 (test 4).

BioFors has no unused within-blot manipulated images left, so the manipulated blots here are made
by code from clean blots of papers not used before (pilot, tests 2-3):
  - splice: the right part of the blot is replaced by the right part of another clean blot from the
    same paper (resized to the same height), joined with no gap;
  - duplication: one lane-wide vertical strip is copied over another lane (half of them flipped);
  - painting: a background patch away from the darkest bands is flattened to its median gray with a
    softened edge.
The same number of untouched clean blots from other new papers are the negatives. Every image
(manipulated or not) is re-saved as JPEG quality 85 at native resolution so compression is identical.
Richardson: 30 more unused August 2026 within-blot images (recall only).
"""
import csv, hashlib, io, json, random, re, sys, tarfile, zipfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from views import views
Image.MAX_IMAGE_PIXELS = None
S = Path(sys.argv[1]); ANN = S / "bf"; ITEMS = S / "test4/items4"; KEY = S / "test4_key"
rng = random.Random(4044); nrng = np.random.default_rng(4044)
old = []
for f in ["pilot_key/key.json", "test2_key/key.json", "test3_key/key.json"]:
    old += json.load(open(S / f))
old_papers = {k["paper"] for k in old if "paper" in k}; old_files = {k["file"] for k in old if "file" in k}

def ok(img):
    g = np.asarray(img.convert("L")); return min(img.size) >= 40 and (g < 128).mean() <= 0.5

cls = json.loads((ANN / "classification.json").read_text())
flagged = set()
for t in ["idd", "cstd", "edd"]:
    flagged |= set(json.loads((ANN / f"{t}_gt.json").read_text()))
clean = {p: sorted(n for n, k in ims.items() if k == "Blot/Gel") for p, ims in cls.items() if p not in flagged and p not in old_papers}
clean = {p: v for p, v in clean.items() if len(v) >= 2}
cp = rng.sample(sorted(clean), 300)
need = {(p, n) for p in cp for n in clean[p]}
imgs = {}
with tarfile.open(S / "raw/biofors/biofors_images.tar") as tar:
    for m in tar:
        k = tuple(Path(m.name).parts[-2:])
        if m.isfile() and k in need:
            im = Image.open(tar.extractfile(m)); im.load(); imgs[k] = im.convert("L")
usable = {p: [n for n in clean[p] if (p, n) in imgs and ok(imgs[(p, n)])] for p in cp}

def splice(p, n):
    a = np.asarray(imgs[(p, n)]).astype(np.float32); h, w = a.shape
    donors = [m for m in usable[p] if m != n]
    if not donors: return None
    b = np.asarray(imgs[(p, rng.choice(donors))]).astype(np.float32)
    b = cv2.resize(b, (max(1, round(b.shape[1] * h / b.shape[0])), h), interpolation=cv2.INTER_AREA)
    x0 = int(w * rng.uniform(0.35, 0.65)); right = b[:, int(b.shape[1] * rng.uniform(0.3, 0.6)):]
    width_right = min(right.shape[1], w - x0)
    if width_right < 0.2 * w: return None
    out = np.concatenate([a[:, :x0], right[:, :width_right]], 1)
    return out, [[(x0 - 2) / out.shape[1], 0, (x0 + 2) / out.shape[1], 1]]

def duplicate(p, n):
    a = np.asarray(imgs[(p, n)]).astype(np.float32).copy(); h, w = a.shape
    lw = max(6, int(w * rng.uniform(0.12, 0.2)))
    xs = int(rng.uniform(0, w / 2 - lw)); xd = int(rng.uniform(w / 2, w - lw))
    if rng.random() < 0.5: xs, xd = xd, xs
    strip = a[:, xs:xs + lw].copy()
    if rng.random() < 0.5: strip = strip[:, ::-1]
    a[:, xd:xd + lw] = strip
    return a, [[xs / w, 0, (xs + lw) / w, 1], [xd / w, 0, (xd + lw) / w, 1]]

def paint(p, n):
    a = np.asarray(imgs[(p, n)]).astype(np.float32).copy(); h, w = a.shape
    blur = cv2.GaussianBlur(a, (0, 0), 2)
    for _ in range(40):
        pw, ph = int(w * rng.uniform(0.15, 0.3)), int(h * rng.uniform(0.25, 0.45))
        x, y = rng.randrange(0, w - pw), rng.randrange(0, h - ph)
        reg = blur[y:y + ph, x:x + pw]
        if reg.min() > np.percentile(blur, 40):          # background only: lighter than the darker 40% of the blot
            break
    else:
        return None
    mask = np.zeros_like(a); mask[y:y + ph, x:x + pw] = 1
    mask = cv2.GaussianBlur(mask, (0, 0), 1.2)
    a = a * (1 - mask) + np.median(reg) * mask
    return a, [[x / w, y / h, (x + pw) / w, (y + ph) / h]]

def jpeg(arr):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return Image.open(io.BytesIO(buf.getvalue()))

key = []
def emit(img, task, extra):
    h = hashlib.sha1(f"{task}{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / task; d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{h}{suffix}.png")
    key.append({"task": task, "id": h, **extra, "size": list(img.size)})

papers = [p for p in cp if usable[p]]; rng.shuffle(papers)
plan = ["splice"] * 10 + ["duplication"] * 10 + ["painting"] * 10
fns = {"splice": splice, "duplication": duplicate, "painting": paint}
pi = 0
for kind in plan:
    while True:
        p = papers[pi]; pi += 1; n = rng.choice(usable[p]); r = fns[kind](p, n)
        if r is not None: break
    arr, boxes = r
    emit(jpeg(arr), "A_biofors", {"label": 1, "paper": p, "image": n, "types": [kind], "boxes_frac": boxes})
neg = 0
while neg < 30:
    p = papers[pi]; pi += 1; n = rng.choice(usable[p])
    emit(jpeg(np.asarray(imgs[(p, n)]).astype(np.float32)), "A_biofors", {"label": 0, "paper": p, "image": n, "types": [], "boxes_frac": []})
    neg += 1

rich = S / "raw/rich_aug"
rows = list(csv.DictReader(open(rich / "260825_catch_all_spreadsheet.csv")))
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
used_r = old_files | {k["file"] for k in json.load(open(S / "test3_key/key.json")) if "file" in k}
w = [r for r in rows if not cross.search(r["summary"]) and r["original_image_filename"] not in used_r]
z = zipfile.ZipFile(rich / "260825_original_images.zip"); names = {Path(n).name: n for n in z.namelist()}
w = [r for r in w if r["original_image_filename"] in names]
paintr = [r for r in w if "paint" in r["summary"].lower()]; other = [r for r in w if "paint" not in r["summary"].lower()]
rng.shuffle(paintr); rng.shuffle(other)
for group, cnt_target in ((paintr, 15), (other, 15)):
    cnt = 0
    for r in group:
        im = Image.open(io.BytesIO(z.read(names[r["original_image_filename"]]))); im.load()
        if min(im.size) < 60: continue
        emit(im, "R_recall", {"label": 1, "summary": r["summary"], "file": r["original_image_filename"], "catalog": r["catalog_number"], "vendor": r["vendor"]})
        cnt += 1
        if cnt == cnt_target: break
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
A = [k for k in key if k["task"] == "A_biofors"]
print(Counter((k["task"], k["label"]) for k in key), Counter(k["types"][0] for k in A if k["label"]))
for lab in (1, 0):
    s = np.array([k["size"] for k in A if k["label"] == lab]); print(f"label {lab}: median size {np.median(s[:,0]):.0f}x{np.median(s[:,1]):.0f}")
print("papers used:", len({k['paper'] for k in A}))

"""Build blind pilot sets: hashed images in items/, labels in key/ (never shown to judges)."""
import csv, hashlib, io, json, random, re, sys, tarfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from views import views
Image.MAX_IMAGE_PIXELS = None

S = Path(sys.argv[1]); RAW = S / "raw"; ANN = S / "bf"
OUT = S / "pilot"; ITEMS = OUT / "items"; KEY = S / "pilot_key"
rng = random.Random(7)

def ok(img):
    g = np.asarray(img.convert("L"))
    return min(img.size) >= 40 and (g < 128).mean() <= 0.5

def save_views(img, d, stem):
    d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{stem}{suffix}.png")

def save(img, tag):
    h = hashlib.sha1(f"{tag}{rng.random()}".encode()).hexdigest()[:10]
    save_views(img, ITEMS / tag.split(":")[0], h)
    return h, None, None

cls = json.loads((ANN / "classification.json").read_text())
blot = {(p, n) for p, ims in cls.items() for n, k in ims.items() if k == "Blot/Gel"}
gt = {t: json.loads((ANN / f"{t}_gt.json").read_text()) for t in ["idd", "cstd", "edd"]}
flagged = set().union(*map(set, gt.values()))
posA = {}
for t in ["idd", "cstd"]:
    for p, v in gt[t].items():
        for n, boxes in v.items():
            if (p, n) in blot: posA.setdefault((p, n), {})[t] = boxes
pairs = [(p, *k.split(), v) for p, d in gt["edd"].items() for k, v in d.items()
         if all((p, x) in blot for x in k.split())]
clean = {}
for p, ims in cls.items():
    if p in flagged: continue
    b = sorted(n for n, k in ims.items() if k == "Blot/Gel")
    if len(b) >= 2: clean[p] = b

need = set(posA) | {(p, a) for p, a, b, _ in pairs} | {(p, b) for p, a, b, _ in pairs}
cp = rng.sample(sorted(clean), 120)
for p in cp: need |= {(p, n) for n in clean[p]}
imgs = {}
with tarfile.open(RAW / "biofors" / "biofors_images.tar") as tar:
    for m in tar:
        k = tuple(Path(m.name).parts[-2:])
        if m.isfile() and k in need:
            im = Image.open(tar.extractfile(m)); im.load(); imgs[k] = im

key = []
# Task A: 30 manipulated (one per paper first), 30 clean (one per paper)
pa = [k for k in sorted(posA) if k in imgs and ok(imgs[k])]; rng.shuffle(pa)
seen, selA = set(), []
for k in pa:
    if k[0] not in seen: selA.append(k); seen.add(k[0])
for k in pa:
    if len(selA) >= 30: break
    if k not in selA: selA.append(k)
selA = selA[:30]
negA = []
for p in cp:
    c = [n for n in clean[p] if (p, n) in imgs and ok(imgs[(p, n)])]
    if c: negA.append((p, rng.choice(c)))
    if len(negA) == 30: break
for k, lab in [(k, 1) for k in selA] + [(k, 0) for k in negA]:
    h, s, size = save(imgs[k], "A_biofors")
    w0, h0 = imgs[k].size
    boxes = [b for t in posA.get(k, {}).values() for b in t]
    key.append({"task": "A_biofors", "id": h, "label": lab, "paper": k[0], "image": k[1],
                "types": sorted(posA.get(k, {})), "boxes_frac": [[b[0]/w0, b[1]/h0, b[2]/w0, b[3]/h0] for b in boxes]})
# Task B: 15 EDD pairs (distinct papers), 15 same-paper clean pairs
rng.shuffle(pairs); selB, seen = [], set()
for p, a, b, v in pairs:
    if p in seen or (p, a) not in imgs or (p, b) not in imgs: continue
    if not (ok(imgs[(p, a)]) and ok(imgs[(p, b)])): continue
    selB.append((p, a, b, v)); seen.add(p)
    if len(selB) == 15: break
negB = []
for p in cp[::-1]:
    c = [n for n in clean[p] if (p, n) in imgs and ok(imgs[(p, n)])]
    if len(c) >= 2: a, b = rng.sample(c, 2); negB.append((p, a, b, None))
    if len(negB) == 15: break
for (p, a, b, v), lab in [(x, 1) for x in selB] + [(x, 0) for x in negB]:
    pid = hashlib.sha1(f"{p}{a}{b}{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / "B_biofors" / pid
    for i, n in enumerate([a, b], 1):
        save_views(imgs[(p, n)], d, f"image{i}")
    key.append({"task": "B_biofors", "id": pid, "label": lab, "paper": p, "images": [a, b]})
# Richardson within-blot positives (recall only): 20
rich = RAW / "rich"
rows = list(csv.DictReader(open(rich / "260605_catch_all_spreadsheet.csv")))
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
w = [r for r in rows if not cross.search(r["summary"])]; rng.shuffle(w)
z = zipfile.ZipFile(rich / "260605_original_images.zip"); names = {Path(n).name: n for n in z.namelist()}
cnt = 0
for r in w:
    n = names.get(r["original_image_filename"])
    if not n: continue
    im = Image.open(io.BytesIO(z.read(n))); im.load()
    h, s, size = save(im, "R_recall")
    key.append({"task": "R_recall", "id": h, "label": 1, "summary": r["summary"], "file": r["original_image_filename"]})
    cnt += 1
    if cnt == 20: break
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
print(Counter((k["task"], k["label"]) for k in key))

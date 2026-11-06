"""Fresh blind test set for rulebook v2 (test 3).
BioFors: the only unused within-blot positives left are thin strips (>= 25 px), from papers not used in
the pilot or test 2; clean blots are size-matched to them so image size gives nothing away.
Richardson: August 2026 release, images not used before, 15 painting + 15 non-painting (recall only).
"""
import csv, hashlib, io, json, random, re, sys, tarfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from views import views
Image.MAX_IMAGE_PIXELS = None
S = Path(sys.argv[1]); ANN = S / "bf"; ITEMS = S / "test3/items3"; KEY = S / "test3_key"
rng = random.Random(3033)
old = json.load(open(S / "pilot_key/key.json")) + json.load(open(S / "test2_key/key.json"))
old_papers = {k["paper"] for k in old if "paper" in k}; old_files = {k["file"] for k in old if "file" in k}
MIN = 25
def ok(img):
    g = np.asarray(img.convert("L")); return min(img.size) >= MIN and (g < 128).mean() <= 0.5

cls = json.loads((ANN / "classification.json").read_text())
blot = {(p, n) for p, ims in cls.items() for n, k in ims.items() if k == "Blot/Gel"}
gt = {t: json.loads((ANN / f"{t}_gt.json").read_text()) for t in ["idd", "cstd", "edd"]}
flagged = set().union(*map(set, gt.values()))
posA = {}
for t in ["idd", "cstd"]:
    for p, v in gt[t].items():
        if p in old_papers: continue
        for n, boxes in v.items():
            if (p, n) in blot: posA.setdefault((p, n), {})[t] = boxes
clean = {p: sorted(n for n, k in ims.items() if k == "Blot/Gel") for p, ims in cls.items() if p not in flagged and p not in old_papers}
clean = {p: v for p, v in clean.items() if v}
cp = rng.sample(sorted(clean), 600)
need = set(posA) | {(p, n) for p in cp for n in clean[p]}
imgs = {}
with tarfile.open(S / "raw/biofors/biofors_images.tar") as tar:
    for m in tar:
        k = tuple(Path(m.name).parts[-2:])
        if m.isfile() and k in need:
            im = Image.open(tar.extractfile(m)); im.load(); imgs[k] = im
pa = [k for k in sorted(posA) if k in imgs and ok(imgs[k])]; rng.shuffle(pa)
sel, seen = [], set()
for k in pa:
    if k[0] not in seen: sel.append(k); seen.add(k[0])
for k in pa:
    if len(sel) >= 30: break
    if k not in sel: sel.append(k)
sel = sel[:30]
# size-matched clean blots: for each positive, the unused clean image (max 1 per paper) closest in height and aspect
pool = [(p, n) for p in cp for n in clean[p] if (p, n) in imgs and ok(imgs[(p, n)])]
used_p, neg = set(), []
for k in sel:
    w0, h0 = imgs[k].size
    cand = [c for c in pool if c[0] not in used_p]
    c = min(cand, key=lambda c: abs(np.log(imgs[c].size[1] / h0)) + abs(np.log((imgs[c].size[0] / imgs[c].size[1]) / (w0 / h0))))
    neg.append(c); used_p.add(c[0])
key = []
def emit(img, task, extra):
    h = hashlib.sha1(f"{task}{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / task; d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{h}{suffix}.png")
    key.append({"task": task, "id": h, **extra, "size": list(img.size)})
for k, lab in [(k, 1) for k in sel] + [(k, 0) for k in neg]:
    w0, h0 = imgs[k].size
    boxes = [b for t in posA.get(k, {}).values() for b in t]
    emit(imgs[k], "A_biofors", {"label": lab, "paper": k[0], "image": k[1], "types": sorted(posA.get(k, {})),
                                "boxes_frac": [[b[0]/w0, b[1]/h0, b[2]/w0, b[3]/h0] for b in boxes]})
rich = S / "raw/rich_aug"
rows = list(csv.DictReader(open(rich / "260825_catch_all_spreadsheet.csv")))
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
w = [r for r in rows if not cross.search(r["summary"]) and r["original_image_filename"] not in old_files]
z = zipfile.ZipFile(rich / "260825_original_images.zip"); names = {Path(n).name: n for n in z.namelist()}
w = [r for r in w if r["original_image_filename"] in names]
paint = [r for r in w if "paint" in r["summary"].lower()]; other = [r for r in w if "paint" not in r["summary"].lower()]
rng.shuffle(paint); rng.shuffle(other)
for group, n in ((paint, 15), (other, 15)):
    cnt = 0
    for r in group:
        im = Image.open(io.BytesIO(z.read(names[r["original_image_filename"]]))); im.load()
        if min(im.size) < 60: continue
        emit(im, "R_recall", {"label": 1, "summary": r["summary"], "file": r["original_image_filename"], "catalog": r["catalog_number"], "vendor": r["vendor"]})
        cnt += 1
        if cnt == n: break
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
A = [k for k in key if k["task"] == "A_biofors"]
print(Counter((k["task"], k["label"]) for k in key))
for lab in (1, 0):
    s = np.array([k["size"] for k in A if k["label"] == lab]); print(f"BioFors label {lab}: median size {np.median(s[:,0]):.0f}x{np.median(s[:,1]):.0f}, papers {len({k['paper'] for k in A if k['label']==lab})}")
print("Richardson vendors:", Counter(k["vendor"] for k in key if k["task"] == "R_recall"))

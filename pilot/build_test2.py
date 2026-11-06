"""Fresh blind test set for rulebook v1: papers and Richardson images not used in the pilot.
items2/<task>/<id>{,_equalized,_local,_residual}.png  -> seen by every condition
tools2/<task>/<id>_rules.png, <id>_measurements.txt   -> seen only by the 'rules + measurements' condition
"""
import csv, hashlib, io, json, random, re, sys, tarfile, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from views import views, equalized, to_gray
from rule_tools import analyse, summary_text, overlay, rule_flags
Image.MAX_IMAGE_PIXELS = None
S = Path(sys.argv[1]); ANN = S / "bf"; ITEMS = S / "test2/items2"; TOOLS = S / "test2/tools2"; KEY = S / "test2_key"
rng = random.Random(2026)
old = json.load(open(S / "pilot_key/key.json"))
old_papers = {k["paper"] for k in old if "paper" in k}; old_files = {k["file"] for k in old if "file" in k}

def ok(img):
    g = np.asarray(img.convert("L")); return min(img.size) >= 40 and (g < 128).mean() <= 0.5

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
cp = rng.sample(sorted(clean), 120)
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
neg = []
for p in cp:
    c = [n for n in clean[p] if (p, n) in imgs and ok(imgs[(p, n)])]
    if c: neg.append((p, rng.choice(c)))
    if len(neg) == 30: break

key = []
def emit(img, task, extra):
    h = hashlib.sha1(f"{task}{rng.random()}".encode()).hexdigest()[:10]
    d = ITEMS / task; d.mkdir(parents=True, exist_ok=True)
    for suffix, im in views(img).items(): im.save(d / f"{h}{suffix}.png")
    a = analyse(img); t = TOOLS / task; t.mkdir(parents=True, exist_ok=True)
    overlay(a, Image.fromarray(equalized(to_gray(img)))).save(t / f"{h}_rules.png")
    (t / f"{h}_measurements.txt").write_text(summary_text(a))
    key.append({"task": task, "id": h, **extra, "flags": rule_flags(a),
                "top_outline": a["pairs"][0]["outline"] if a["pairs"] else 0.0})
for k, lab in [(k, 1) for k in sel] + [(k, 0) for k in neg]:
    w0, h0 = imgs[k].size
    boxes = [b for t in posA.get(k, {}).values() for b in t]
    emit(imgs[k], "A_biofors", {"label": lab, "paper": k[0], "image": k[1], "types": sorted(posA.get(k, {})),
                                "boxes_frac": [[b[0]/w0, b[1]/h0, b[2]/w0, b[3]/h0] for b in boxes]})
rich = S / "raw/rich"
rows = list(csv.DictReader(open(rich / "260605_catch_all_spreadsheet.csv")))
cross = re.compile(r"pattern [A-Z]|image_index|identical|same background|Images |different antibod|different clone|both lanes|share|\(\d+ and \d+\)", re.I)
w = [r for r in rows if not cross.search(r["summary"]) and r["original_image_filename"] not in old_files]; rng.shuffle(w)
z = zipfile.ZipFile(rich / "260605_original_images.zip"); names = {Path(n).name: n for n in z.namelist()}
cnt = 0
for r in w:
    n = names.get(r["original_image_filename"])
    if not n: continue
    im = Image.open(io.BytesIO(z.read(n))); im.load()
    emit(im, "R_recall", {"label": 1, "summary": r["summary"], "file": r["original_image_filename"], "catalog": r["catalog_number"]})
    cnt += 1
    if cnt == 20: break
KEY.mkdir(exist_ok=True); (KEY / "key.json").write_text(json.dumps(key, indent=1))
from collections import Counter
print(Counter((k["task"], k["label"]) for k in key), "| Richardson within-blot images left unused:", len(w) - cnt)

import csv, glob, io, json, sys, zipfile
sys.path.insert(0, __import__('os').path.dirname(__file__))
from rich_ann import find_annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
S = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
key = {k["id"]: k for k in json.load(open(S / "pilot_key/key.json"))}
def load(pat):
    d = {}
    for f in glob.glob(str(S / pat)):
        for p in json.load(open(f)): d[p["id"]] = p
    return d
A = load("pilot/runs/run1/A_biofors.json"); B = load("pilot/runs/run1/B_*.json")
R1 = load("pilot/runs/run1/R_recall_*.json"); R2 = load("pilot/runs/run2_vendor/*.json")
font = ImageFont.load_default(size=18); small = ImageFont.load_default(size=15)
W = 420
def fit(im, h=None):
    im = im.convert("RGB"); s = W / im.width
    return im.resize((W, max(1, round(im.height * s))))
def boxes(im, fr, color):
    d = ImageDraw.Draw(im)
    for b in fr: d.rectangle([b[0]*im.width, b[1]*im.height, b[2]*im.width, b[3]*im.height], outline=color, width=3)
    return im
def row(panels, labels, caption):
    h = max(p.height for p in panels); w = len(panels) * (W + 10) + 10
    canvas = Image.new("RGB", (w, h + 80), "white"); d = ImageDraw.Draw(canvas)
    d.text((10, 6), caption, fill="black", font=font)
    for i, (p, l) in enumerate(zip(panels, labels)):
        x = 10 + i * (W + 10); d.text((x, 34), l, fill=(90, 90, 90), font=small); canvas.paste(p, (x, 58))
    return canvas
def sheet(rows, name, title):
    for n in range(0, len(rows), 6):
        part = rows[n:n+6]; w = max(r.width for r in part); h = sum(r.height + 20 for r in part) + 50
        c = Image.new("RGB", (w, h), (235, 235, 235)); d = ImageDraw.Draw(c)
        d.text((10, 12), f"{title} ({n+1}-{n+len(part)} of {len(rows)})", fill="black", font=font)
        y = 50
        for r in part: c.paste(r, (0, y)); y += r.height + 20
        f = OUT / f"{name}_{n//6+1}.png"; c.save(f); print(f)
img = lambda t, i, s="": Image.open(S / f"pilot/items/{t}/{i}{s}.png")
# A misses and false alarms
for lab, want, name, title in [(1, "legitimate", "A_missed", "Single blots I MISSED (red = BioFors ground-truth box)"),
                               (0, "manipulated", "A_false_alarms", "Clean single blots I FLAGGED (blue = where I pointed)")]:
    rows = []
    for i, p in A.items():
        k = key[i]
        if k["label"] != lab or p["verdict"] != want: continue
        o = fit(img("A_biofors", i)); st = fit(img("A_biofors", i, "_equalized"))
        if lab: boxes(o, k["boxes_frac"], "red"); boxes(st, k["boxes_frac"], "red")
        else: boxes(o, p["regions"], "blue"); boxes(st, p["regions"], "blue")
        t = "+".join({"idd": "duplication within image", "cstd": "splice / sharp transition"}[x] for x in k["types"]) if lab else "clean (paper with nothing flagged)"
        rows.append(row([o, st], ["image", "equalized (background revealed)"], f"{i}  truth: {t}  |  my p(manipulated) = {p['probability_manipulated']:.2f}"))
    sheet(rows, name, title)
# B misses
rows = []
for i, p in B.items():
    if key[i]["label"] != 1 or p["verdict"] == "shared_content": continue
    d = S / "pilot/items/B_biofors" / i
    rows.append(row([fit(Image.open(d / "image1.png")), fit(Image.open(d / "image2.png"))], ["image 1", "image 2"],
                    f"{i}  truth: reused content (BioFors EDD)  |  my p(shared) = {p['probability_shared']:.2f}"))
sheet(rows, "B_missed_pairs", "Blot pairs I MISSED")
# Richardson misses (missed in both runs), with Richardson's annotation
rich = S / "raw/rich"; rows_csv = {r["original_image_filename"]: r for r in csv.DictReader(open(rich / "260605_catch_all_spreadsheet.csv"))}
za = zipfile.ZipFile(rich / "260605_annotated_images.zip"); an = {Path(n).name: n for n in za.namelist()}
rows = []
for i in R1:
    if R1[i]["verdict"] == "manipulated" or R2[i]["verdict"] == "manipulated": continue
    k = key[i]; r = rows_csv[k["file"]]; panels = [fit(img("R_recall", i)), fit(img("R_recall", i, "_equalized"))]
    labels = ["image", "equalized (background revealed)"]
    for n in find_annotations(za.namelist(), r)[:1]:
        panels.append(fit(Image.open(io.BytesIO(za.read(n))))); labels.append("Richardson's annotation")
    rows.append(row(panels, labels, f"{i}  {r['catalog_number']}  truth: {r['summary'][:70]}  |  my p = {R1[i]['probability_manipulated']:.2f} / {R2[i]['probability_manipulated']:.2f}"))
sheet(rows, "R_missed", "Richardson vendor blots I MISSED in both runs")

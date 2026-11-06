"""Run the rule measurements on the pilot (dev) set: overlays + how often each rule fires per class."""
import json, sys, tarfile, io, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from rule_tools import analyse, summary_text, overlay, rule_flags
from views import equalized, to_gray
Image.MAX_IMAGE_PIXELS = None
S = Path(sys.argv[1]); out = S / "dev_rules"; out.mkdir(exist_ok=True)
key = [k for k in json.load(open(S / "pilot_key/key.json")) if k["task"] in ("A_biofors", "R_recall")]
need = {(k["paper"], k["image"]) for k in key if k["task"] == "A_biofors"}
imgs = {}
with tarfile.open(S / "raw/biofors/biofors_images.tar") as tar:
    for m in tar:
        t = tuple(Path(m.name).parts[-2:])
        if m.isfile() and t in need:
            im = Image.open(tar.extractfile(m)); im.load(); imgs[t] = im
z = zipfile.ZipFile(S / "raw/rich/260605_original_images.zip"); zn = {Path(n).name: n for n in z.namelist()}
rows = []
for k in key:
    im = imgs[(k["paper"], k["image"])] if k["task"] == "A_biofors" else Image.open(io.BytesIO(z.read(zn[k["file"]])))
    a = analyse(im)
    eq = Image.fromarray(equalized(to_gray(im)))
    overlay(a, eq).save(out / f"{k['id']}_rules.png")
    (out / f"{k['id']}.txt").write_text(summary_text(a))
    f = rule_flags(a); top = a["pairs"][0]["outline"] if a["pairs"] else 0
    rows.append({**f, "task": k["task"], "label": k["label"], "types": k.get("types", []), "id": k["id"], "nbands": len(a["bands"]), "top_sim": top})
json.dump(rows, open(out / "flags.json", "w"))
for task in ("A_biofors", "R_recall"):
    for lab in (1, 0):
        r = [x for x in rows if x["task"] == task and x["label"] == lab]
        if not r: continue
        fire = lambda c: sum(x[c] > 0 for x in r)
        print(f"{task} label={lab} n={len(r)}: dup>=0.95 fires {fire('dup_pairs')}, line fires {fire('lines')}, stripe fires {fire('stripes')}, flat fires {fire('flat_patches')}, "
              f"any {sum(any(x[c] > 0 for c in ('dup_pairs','lines','flat_patches')) for x in r)} | median bands {np.median([x['nbands'] for x in r]):.0f}")

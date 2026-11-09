import json, io, zipfile, sys
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))
from screen_scraped import dhash, hamming
z = zipfile.ZipFile("raw/rich_aug/260825_original_images.zip"); names = {n.split("/")[-1]: n for n in z.namelist()}
cache = {}
def load(m):
    k = (m["src"], m["file"])
    if k not in cache:
        im = Image.open("scraped/images/" + m["file"]) if m["src"] == "scraped" else Image.open(io.BytesIO(z.read(names[m["file"]])))
        cache[k] = np.asarray(im.convert("L"))
    return cache[k]
def panel(m):
    x, y, w, h = m["box"]; return load(m)[y:y+h, x:x+w].astype(np.float32)
pairs = json.load(open(sys.argv[1])); out = []
for d in pairs:
    A, B = d["a"], d["b"]
    ga, gb = load(A), load(B)
    hd = hamming(dhash(Image.fromarray(ga)), dhash(Image.fromarray(gb)))
    pa, pb = panel(A), panel(B); pb = cv2.resize(pb, (pa.shape[1], pa.shape[0]), interpolation=cv2.INTER_AREA)
    # content: smoothed panels (bands) compared; low-pass so grain does not count
    la, lb = cv2.GaussianBlur(pa, (0, 0), 3), cv2.GaussianBlur(pb, (0, 0), 3)
    content = float(np.abs(la - lb).mean())
    same_item = A["item"] == B["item"]
    kind = "same panel twice" if same_item else ("same image" if hd <= 6 and content < 4 else "different content")
    out.append({**d, "dhash": hd, "content_diff": round(content, 1), "kind": kind})
json.dump(out, open(sys.argv[2], "w"), indent=1)
from collections import Counter
print(Counter(o["kind"] for o in out))
print(Counter((o["kind"], tuple(sorted((o["a"]["src"][:9], o["b"]["src"][:9])))) for o in out))

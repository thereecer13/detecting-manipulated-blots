"""Copied-block scan of Thermo ICC/IF images (duplicated cells inside one image).
Uses proteintech/block_clone.py without the Proteintech watermark mask and with a longer search range.
  python3 if_clone.py index.jsonl images_dir out.json [--n N --seed S] [--jobs 3]
Only vendor images with app ICC or IF are scanned. Resumable."""
import argparse, json, random, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent.parent / 'proteintech')); sys.path.insert(0, str(Path(__file__).parent.parent))
import block_clone as B
B.MAX_DIST = 320
def scan(path):
    try:
        rgb = np.asarray(Image.open(path).convert("RGB")); g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
        valid = np.ones(g.shape, bool)
        return {"size": [rgb.shape[1], rgb.shape[0]], "found": B.verify(rgb, g, valid, B.candidates(g, valid))}
    except Exception as e: return {"error": str(e)[:80]}
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("index"); ap.add_argument("images"); ap.add_argument("out")
    ap.add_argument("--n", type=int); ap.add_argument("--seed", type=int, default=1); ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args(); seen = set(); rows = []
    for l in open(a.index):
        r = json.loads(l)
        if r.get("app") in ("ICC", "IF") and r.get("file") and r["file"] not in seen: seen.add(r["file"]); rows.append(r)
    if a.n: random.seed(a.seed); rows = random.sample(rows, a.n)
    done = {r["file"]: r for r in json.load(open(a.out))} if Path(a.out).exists() else {}
    todo = [r for r in rows if r["file"] not in done]
    with ProcessPoolExecutor(a.jobs) as ex:
        for i, (r, f) in enumerate(zip(todo, ex.map(scan, [f"{a.images}/{r['file']}" for r in todo], chunksize=2))):
            done[r["file"]] = dict(r, **f)
            if i % 50 == 49 or i == len(todo) - 1: json.dump(list(done.values()), open(a.out, "w")); print(i + 1, "/", len(todo), flush=True)
    print(len(done), "images,", sum(bool(r.get("found")) for r in done.values()), "flagged")

"""Sample Thermo antibody product pages and collect microscopy figures that contain a no-primary /
secondary-only control panel.

For each sampled product page: every gallery entry (catalog, image URL, application, description) is
appended to <out>/media.jsonl; entries whose description mentions a no-primary or secondary-only
control (and are not WB / flow) are downloaded to <out>/images/ and listed in <out>/index.jsonl.
Pages are not cached (they are ~700 kB each). robots.txt is obeyed, one request per --delay seconds,
honest User-Agent; resumable (products already in media.jsonl or done.txt are skipped).

    python pilot/sample_controls.py --out ctrl_sample --per-prefix PA5-=2000 MA5-=1000 OTHER=500 \
        [--skip media_all.jsonl] [--seed 1]
"""
import argparse, hashlib, json, random, re, sys, time, urllib.error, urllib.request, urllib.robotparser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import scrape_vendors as sv
from thermo_media import items

UA = sv.UA
CTRL = re.compile(r"no[\s-]*primary|secondary[\s-]*(antibody)?[\s-]*only|without (the )?primary|primary antibody (was )?omitted|instead of the primary", re.I)
_last = [0.0]


def get(url, delay):
    wait = delay - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--per-prefix", nargs="+", required=True)
    ap.add_argument("--skip", type=Path, nargs="*", default=[]); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--delay", type=float, default=6.0); ap.add_argument("--cache", type=Path, default=Path("scraped/cache"), help="sitemap cache")
    a = ap.parse_args(); (a.out / "images").mkdir(parents=True, exist_ok=True)
    rp = urllib.robotparser.RobotFileParser(); rp.parse(get("https://www.thermofisher.com/robots.txt", 0).decode("utf-8", "ignore").splitlines())
    prods = sv.thermo_products(sv.Fetcher(a.cache, 3.0))
    skip = set()
    for f in a.skip: skip |= {json.loads(l)["catalog"] for l in f.read_text().splitlines()}
    done_f = a.out / "done.txt"; done = set(done_f.read_text().split()) if done_f.exists() else set()
    rng = random.Random(a.seed); targets = dict(kv.split("=") for kv in a.per_prefix)
    by = {}
    for cat, url in sorted(set(prods)):
        k = next((p for p in targets if p != "OTHER" and cat.upper().startswith(p)), "OTHER")
        by.setdefault(k, []).append((cat, url))
    plan = []
    for k, n in targets.items():
        pool = [x for x in by.get(k, []) if x[0] not in skip]; rng.shuffle(pool); plan += pool[:int(n)]
    rng.shuffle(plan)
    print(f"{len(plan)} products planned, {len(done)} already done", flush=True)
    for i, (cat, url) in enumerate(plan):
        if cat in done: continue
        if not rp.can_fetch(UA, url): continue
        try: page = get(url, a.delay).decode("utf-8", "ignore")
        except Exception as e: print("  skip", cat, str(e)[:60], flush=True); page = ""
        n_ctrl = 0
        with (a.out / "media.jsonl").open("a") as mf:
            for it in items(page):
                mf.write(json.dumps(it) + "\n")
                if it["app"] in ("WB", "Flow", "FC", "ELISA") or not CTRL.search(it["description"]): continue
                fn = hashlib.sha1(it["url"].encode()).hexdigest()[:12] + ".jpg"
                if not (a.out / "images" / fn).exists():
                    try: (a.out / "images" / fn).write_bytes(get(it["url"], a.delay))
                    except Exception as e: print("  img fail", it["url"], str(e)[:60], flush=True); continue
                with (a.out / "index.jsonl").open("a") as xf: xf.write(json.dumps({**it, "file": fn}) + "\n")
                n_ctrl += 1
        with done_f.open("a") as df: df.write(cat + "\n")
        print(f"  [{i + 1}/{len(plan)}] {cat}" + (f"  {n_ctrl} control figure(s)" if n_ctrl else ""), flush=True)


if __name__ == "__main__":
    main()

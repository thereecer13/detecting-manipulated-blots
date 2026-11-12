"""Crawl every Thermo PA5- / MA5- antibody product page and download all ICC / IF figures (controls or not).

The sample in pilot/controls/ found no-primary control panels only on PA5- and MA5- products (80 of
3,000 sampled pages, 0 of 500 other prefixes). This crawls the rest of those two families:
  * page gallery entries -> <out>/media.jsonl (all applications)
  * every microscopy figure (app ICC / IF, or a description that says immunofluorescence /
    immunocytochemistry) -> <out>/images/, listed in <out>/index.jsonl with "control": true when the
    description mentions a no-primary / secondary-only control
  * every western blot figure -> <out>/wb/images/, listed in <out>/wb/scraped.jsonl in the format of
    scrape_vendors.py (so template_scan2.py can scan it); blot URLs already listed in --have-wb files
    are not downloaded again
Order: MA5- first (higher control rate), then PA5-, shuffled within each (seed 1).
Products already listed in --skip media files or <out>/done.txt are not fetched again; ICC entries from
--skip media files are still downloaded (image only). robots.txt is obeyed, honest User-Agent, one
request per --delay seconds, back-off on HTTP 429 / 5xx. Resumable.

    python pilot/crawl_icc.py --out icc_all --skip media_all.jsonl ctrl_sample/media.jsonl --delay 2 \
        --have-wb scraped_tmpl/scraped.jsonl scraped_ma5/scraped.jsonl scraped_members/scraped.jsonl
"""
import argparse, hashlib, json, random, re, sys, time, urllib.error, urllib.request, urllib.robotparser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import scrape_vendors as sv
from thermo_media import items
from sample_controls import CTRL

UA = sv.UA
MICRO = re.compile(r"immunofluorescen|immunocytochem|\bICC\b|confocal", re.I)
_last = [0.0]


def get(url, delay, tries=4):
    for k in range(tries):
        wait = delay - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and k < tries - 1: time.sleep(60 * (k + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if k < tries - 1: time.sleep(30 * (k + 1)); continue
            raise


def is_micro(it):
    if it["app"] in ("WB", "Flow", "FC", "ELISA", "IP", "ChIP", "IHC"): return False
    return it["app"] in ("ICC", "IF", "ICC/IF") or bool(MICRO.search(it["description"] or ""))


def is_wb(it):
    return it["app"] == "WB" or (it["app"] is None and bool(re.search(r"western blot", it["description"] or "", re.I)))


def fetch_wb(it, out, delay, have_wb, product_url=None):
    if it["url"] in have_wb: return
    fn = hashlib.sha1(it["url"].encode()).hexdigest()[:12] + ".jpg"; p = out / "wb" / "images" / fn
    if not p.exists():
        try: p.write_bytes(get(it["url"], delay))
        except Exception as e: print("  wb fail", it["url"], str(e)[:60], flush=True); return
    pre = it["catalog"][:4]
    with (out / "wb" / "scraped.jsonl").open("a") as f:
        f.write(json.dumps({"vendor": "thermo", "prefix": pre, "catalog": it["catalog"], "product_url": product_url, "image_url": it["url"],
                            "alt": it["description"][:200] if it["description"] else "", "file": fn, "fetched": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())}) + "\n")
    have_wb.add(it["url"])


def fetch_image(it, out, delay, have):
    fn = hashlib.sha1(it["url"].encode()).hexdigest()[:12] + ".jpg"
    if fn in have: return
    p = out / "images" / fn
    if not p.exists():
        try: p.write_bytes(get(it["url"], delay))
        except Exception as e: print("  img fail", it["url"], str(e)[:60], flush=True); return
    with (out / "index.jsonl").open("a") as xf:
        xf.write(json.dumps({**it, "file": fn, "control": bool(CTRL.search(it["description"] or ""))}) + "\n")
    have.add(fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--skip", type=Path, nargs="*", default=[])
    ap.add_argument("--delay", type=float, default=2.0); ap.add_argument("--have-wb", type=Path, nargs="*", default=[]); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cache", type=Path, default=Path("scraped/cache"), help="sitemap cache")
    a = ap.parse_args(); (a.out / "images").mkdir(parents=True, exist_ok=True); (a.out / "wb" / "images").mkdir(parents=True, exist_ok=True)
    have_wb = set()
    for f in a.have_wb + [a.out / "wb" / "scraped.jsonl"]:
        if f.exists(): have_wb |= {json.loads(l)["image_url"] for l in f.read_text().splitlines() if l.strip()}
    rp = urllib.robotparser.RobotFileParser(); rp.parse(get("https://www.thermofisher.com/robots.txt", 0).decode("utf-8", "ignore").splitlines())
    idx = a.out / "index.jsonl"
    have = {json.loads(l)["file"] for l in idx.read_text().splitlines()} if idx.exists() else set()
    # 1. images of products crawled before (no page fetch)
    skip = set(); old = []; old_wb = []
    for f in a.skip:
        for l in f.read_text().splitlines():
            it = json.loads(l); skip.add(it["catalog"])
            if it["catalog"].startswith(("PA5-", "MA5-")) and is_micro(it): old.append(it)
            if it["catalog"].startswith(("PA5-", "MA5-")) and is_wb(it): old_wb.append(it)
    old = list({it["url"]: it for it in old}.values())
    print(f"{len(old)} microscopy figures from earlier crawls", flush=True)
    for it in old: fetch_image(it, a.out, a.delay, have)
    # 2. remaining product pages
    done_f = a.out / "done.txt"; done = set(done_f.read_text().split()) if done_f.exists() else set()
    prods = sorted(set(sv.thermo_products(sv.Fetcher(a.cache, 3.0))))
    rng = random.Random(a.seed); plan = []
    for pre in ("MA5-", "PA5-"):
        pool = [x for x in prods if x[0].startswith(pre) and x[0] not in skip]; rng.shuffle(pool); plan += pool
    print(f"{len(plan)} product pages planned, {len(done)} already done", flush=True)
    for i, (cat, url) in enumerate(plan):
        if cat in done or not rp.can_fetch(UA, url): continue
        try: page = get(url, a.delay).decode("utf-8", "ignore")
        except Exception as e: print("  skip", cat, str(e)[:60], flush=True); page = ""
        n = 0
        with (a.out / "media.jsonl").open("a") as mf:
            for it in items(page):
                mf.write(json.dumps(it) + "\n")
                if is_micro(it): fetch_image(it, a.out, a.delay, have); n += 1
                elif is_wb(it): fetch_wb(it, a.out, a.delay, have_wb, url)
        with done_f.open("a") as df: df.write(cat + "\n")
        if n or i % 50 == 0: print(f"  [{i + 1}/{len(plan)}] {cat}" + (f"  {n} microscopy figure(s)" if n else ""), flush=True)
    # 3. blots of products crawled before (image only), after the new pages
    old_wb = [it for it in {it["url"]: it for it in old_wb}.values() if it["url"] not in have_wb]
    print(f"{len(old_wb)} blot images from earlier crawls not yet downloaded", flush=True)
    for k, it in enumerate(old_wb):
        fetch_wb(it, a.out, a.delay, have_wb)
        if k % 200 == 0: print(f"  old blots {k}/{len(old_wb)}", flush=True)


if __name__ == "__main__":
    main()

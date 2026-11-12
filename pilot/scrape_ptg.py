"""Polite scraper for Proteintech (ptglab.com) antibody product pages: saves the IHC images.

Product URLs come from the site's product sitemaps; antibody pages are sampled at random (seeded).
robots.txt is obeyed, one request per --delay seconds, honest User-Agent; resumable (products in
<out>/done.txt are skipped). Images are for private research use and are not redistributed.

    python pilot/scrape_ptg.py --urls product_urls.txt --out ptg_ihc --n 600 [--seed 1] [--apps IHC]
"""
import argparse, hashlib, json, random, re, sys, time, urllib.request, urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from scrape_vendors import UA

BASE = "https://www.ptglab.com"
ANTIBODY = re.compile(r"/products/[^/]*Antibody-[A-Za-z0-9]+-\d+-[A-Za-z]+\.htm$")
_last = [0.0]


def get(url, delay):
    wait = delay - (time.time() - _last[0])
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--n", type=int, default=600); ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--delay", type=float, default=4.0); ap.add_argument("--apps", default="IHC")
    a = ap.parse_args(); (a.out / "images").mkdir(parents=True, exist_ok=True)
    rp = urllib.robotparser.RobotFileParser(); rp.parse(get(BASE + "/robots.txt", 0).decode("utf-8", "ignore").splitlines())
    urls = sorted({u.strip() for u in a.urls.read_text().splitlines() if ANTIBODY.search(u.strip())})
    random.Random(a.seed).shuffle(urls); urls = urls[:a.n]
    done_f = a.out / "done.txt"; done = set(done_f.read_text().split()) if done_f.exists() else set()
    app_re = re.compile(rf"/products/pictures/[^\"'\s]+?-(?:{a.apps})[-_]?\d*[^\"'\s/]*?\.jpg", re.I)
    print(f"{len(urls)} antibody pages planned, {len(done)} done", flush=True)
    for i, url in enumerate(urls):
        if url in done or not rp.can_fetch(UA, url): continue
        try: page = get(url, a.delay).decode("utf-8", "ignore")
        except Exception as e: print("  skip", url, str(e)[:60], flush=True); page = ""
        imgs = sorted({m.group(0) for m in app_re.finditer(page)})
        cat = re.search(r"Antibody-([A-Za-z0-9]+-\d+-[A-Za-z]+)\.htm$", url).group(1)
        saved = 0
        for path in imgs:
            iu = BASE + path; fn = hashlib.sha1(iu.encode()).hexdigest()[:12] + ".jpg"
            if not (a.out / "images" / fn).exists():
                try: (a.out / "images" / fn).write_bytes(get(iu, a.delay))
                except Exception as e: print("  img fail", iu, str(e)[:60], flush=True); continue
            with (a.out / "index.jsonl").open("a") as f:
                f.write(json.dumps({"catalog": cat, "product_url": url, "image_url": iu, "file": fn,
                                    "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds")}) + "\n")
            saved += 1
        with done_f.open("a") as f: f.write(url + "\n")
        print(f"  [{i + 1}/{len(urls)}] {cat} ({saved} images)", flush=True)


if __name__ == "__main__":
    main()

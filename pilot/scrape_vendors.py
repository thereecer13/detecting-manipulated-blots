"""Scrape clean (not flagged by Richardson & David) western blot images from antibody vendor catalogs.

Polite by design: obeys robots.txt (including Crawl-delay), waits at least --delay seconds between
requests to a host, sends an honest User-Agent, caches every page so nothing is fetched twice, and
logs the URL, catalog number, alt text and fetch time of every image. Images are for private
research use and are not redistributed.

Vendors (the ones whose product pages are reachable and whose blot images can be found):
  thermo   Thermo Fisher / Invitrogen primary antibodies (catalog prefixes MA5-, PA5-) and Abnova (RAB0)
           on www.thermofisher.com, product URLs from the antibody sitemaps, 650-px image rendition
  origene  Origene primary antibodies (TA8, TA5) on www.origene.com, product URLs from the sitemap

Every catalog number in the Richardson spreadsheet (any vendor, any problem type) is excluded.

    python pilot/scrape_vendors.py --spreadsheet raw/rich_aug/260825_catch_all_spreadsheet.csv \
        --out scraped --per-prefix MA5-=110 PA5-=20 RAB0=20 TA8=70 TA5=60
"""
import argparse, csv, hashlib, html, json, random, re, time, urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import urllib.request

UA = "blot-integrity-research/0.1 (academic image-integrity study; low-rate, robots.txt-compliant)"


class Fetcher:
    def __init__(self, cache: Path, delay: float):
        self.cache = cache; self.cache.mkdir(parents=True, exist_ok=True)
        self.delay = delay; self.last = {}; self.robots = {}

    def _robots(self, host):
        if host not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                rp.parse(self._get(f"https://{host}/robots.txt", check=False).decode("utf-8", "ignore").splitlines())
            except Exception:
                rp.parse([])
            self.robots[host] = rp
        return self.robots[host]

    def _get(self, url, check=True):
        host = urlparse(url).netloc
        if check:
            rp = self._robots(host)
            if not rp.can_fetch(UA, url):
                raise PermissionError(f"robots.txt disallows {url}")
            wait = max(self.delay, rp.crawl_delay(UA) or 0)
        else:
            wait = self.delay
        dt = time.time() - self.last.get(host, 0)
        if dt < wait: time.sleep(wait - dt)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
        finally:
            self.last[host] = time.time()
        return data

    def get(self, url, binary=False):
        f = self.cache / (hashlib.sha1(url.encode()).hexdigest() + (".bin" if binary else ".html"))
        if f.exists():
            return f.read_bytes()
        data = self._get(url)
        f.write_bytes(data)
        return data


def locs(xml):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)


def norm_cat(c):
    return re.sub(r"[^A-Z0-9]", "", c.upper())


# ---------- vendor: Thermo Fisher (incl. Abnova RAB0) ----------

def thermo_products(F):
    out = []
    for sm in locs(F.get("https://www.thermofisher.com/antibody/sitemap-AntibodiesIndex.xml").decode()):
        for u in locs(F.get(sm).decode()):
            if "/antibody/product/" in u:
                out.append((u.rstrip("/").split("/")[-1], u))
    return out


def thermo_images(page):
    t = page.decode("utf-8", "ignore").replace("\\u003d", "=").replace("\\/", "/")
    files = re.findall(r"/antibody/images/\d+/([^\"'?\s]+?-WB-[^\"'?\s]*?\.(?:jpe?g|png))", t, re.I)
    seen = []
    for f in files:
        if f not in seen: seen.append(f)
    alt = (re.findall(r'alt="([^"]*Western Blot[^"]*)"', t) or [""])[0]
    return [(f"https://www.thermofisher.com/antibody/images/650/{f}", html.unescape(alt)) for f in seen]


# ---------- vendor: Origene ----------

def origene_products(F):
    out = []
    for sm in locs(F.get("https://www.origene.com/media/sitemap/sitemap.xml").decode()):
        for u in locs(F.get(sm).decode()):
            m = re.search(r"/catalog/antibodies/primary-antibodies/(ta\d+|cf\d+)-", u, re.I)
            if m: out.append((m.group(1).upper(), u))
    return out


def origene_images(page):
    """Western blot images from the product gallery data (file names ending in -w, or captions
    mentioning western blots); the page's <img> tags only show the first gallery image."""
    t = page.decode("utf-8", "ignore").replace("\\/", "/")
    res = []
    for full, cap in re.findall(r'"full":"(https://cdn\.origene\.com/[^"]+)","caption":"((?:[^"\\]|\\.)*)"', t):
        url = full.split("?")[0]
        cap = html.unescape(re.sub(r"<[^>]+>", "", cap.encode().decode("unicode_escape", "ignore")))
        if (re.search(r"-w\.(?:jpe?g|png)$", url, re.I) or re.search(r"western|\bWB\b", cap, re.I)) and url not in [u for u, _ in res]:
            res.append((url, cap))
    return res


VENDORS = {"thermo": (thermo_products, thermo_images), "origene": (origene_products, origene_images)}
PREFIX_VENDOR = {"MA5-": "thermo", "PA5-": "thermo", "RAB0": "thermo", "TA8": "origene", "TA5": "origene"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spreadsheet", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--per-prefix", nargs="+", required=True, help="PREFIX=N, e.g. MA5-=110 TA8=70")
    ap.add_argument("--delay", type=float, default=3.0, help="minimum seconds between requests to one host")
    ap.add_argument("--seed", type=int, default=5055)
    a = ap.parse_args()
    flagged = {norm_cat(r["catalog_number"]) for r in csv.DictReader(open(a.spreadsheet, encoding="utf-8"))}
    F = Fetcher(a.out / "cache", a.delay)
    img_dir = a.out / "images"; img_dir.mkdir(parents=True, exist_ok=True)
    log = a.out / "scraped.jsonl"
    done = {json.loads(l)["catalog"] for l in log.read_text().splitlines()} if log.exists() else set()
    targets = dict(kv.split("=") for kv in a.per_prefix)
    rng = random.Random(a.seed)
    products = {}
    for v in {PREFIX_VENDOR[p] for p in targets}:
        products[v] = VENDORS[v][0](F)
        print(f"{v}: {len(products[v])} product URLs in sitemaps")
    for prefix, n in targets.items():
        v = PREFIX_VENDOR[prefix]; n = int(n)
        pool = sorted({(c, u) for c, u in products[v] if c.upper().startswith(prefix) and norm_cat(c) not in flagged})
        rng.shuffle(pool)
        got = sum(1 for c in done if c.upper().startswith(prefix))
        print(f"{prefix}: {len(pool)} unflagged products available, target {n}, already have {got}")
        for cat, url in pool:
            if got >= n: break
            if cat in done: continue
            try:
                imgs = VENDORS[v][1](F.get(url))
                if not imgs: continue
                img_url, alt = imgs[0]                       # one image per product, so no product dominates
                data = F.get(img_url, binary=True)
            except Exception as e:
                print(f"  skip {cat}: {e}"); continue
            name = f"{hashlib.sha1(img_url.encode()).hexdigest()[:12]}{Path(urlparse(img_url).path).suffix or '.jpg'}"
            (img_dir / name).write_bytes(data)
            rec = {"vendor": v, "prefix": prefix, "catalog": cat, "product_url": url, "image_url": img_url,
                   "alt": alt[:300], "file": name, "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with open(log, "a") as f: f.write(json.dumps(rec) + "\n")
            done.add(cat); got += 1
            print(f"  [{prefix} {got}/{n}] {cat}")


if __name__ == "__main__":
    main()

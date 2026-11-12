"""Check Thermo product status ("discontinued": true/false in the product page) for catalog numbers.

    python pilot/check_discontinued.py --catalogs list.txt --out status.jsonl [--delay 6]

Fetches https://www.thermofisher.com/antibody/product/<catalog> (redirects to the product page),
records HTTP status, the status flags of that product (searchStatus, longTermUnavailable, orderable,
discontinued), and the western blot image file names on the page.
Resumable (skips catalogs already in --out). Honest User-Agent, one request per --delay seconds.
"""
import argparse, json, re, time, urllib.error, urllib.request
from pathlib import Path

UA = "blot-integrity-research/0.1 (academic image-integrity study; low-rate, robots.txt-compliant)"


def check(cat):
    url = f"https://www.thermofisher.com/antibody/product/{cat}"
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60)
        b = r.read().decode("utf-8", "ignore"); st = r.status; final = r.geturl()
    except urllib.error.HTTPError as e:
        return {"catalog": cat, "http": e.code, "exists": False}
    except Exception as e:
        return {"catalog": cat, "http": None, "error": str(e)[:80]}
    web = cat.replace("-", "")
    blk = re.search(rf'"webId":"{re.escape(web)}"(.{{0,400}}?)"discontinued":(true|false)', b, re.S)
    fields = {}
    if blk:
        for k in ("searchStatus", "longTermUnavailable", "orderable"):
            m = re.search(rf'"{k}":(true|false)', blk.group(1)); fields[k] = (m.group(1) == "true") if m else None
        fields["discontinued"] = blk.group(2) == "true"
    d = [blk.group(2)] if blk else []
    imgs = sorted(set(re.findall(rf"images/650/({re.escape(cat)}[^\"'?\\ ]*?WB[^\"'?\\ ]*?\.jpg)", b)))
    exists = cat in final and bool(d)
    return {"catalog": cat, "http": st, "final": final, "exists": exists,
            "discontinued": (d[0] == "true") if d else None, **{k: v for k, v in fields.items() if k != "discontinued"}, "wb_images": imgs}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--catalogs", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True); ap.add_argument("--delay", type=float, default=6.0)
    a = ap.parse_args()
    done = {json.loads(l)["catalog"] for l in a.out.read_text().splitlines()} if a.out.exists() else set()
    for cat in [l.strip() for l in a.catalogs.read_text().splitlines() if l.strip()]:
        if cat in done: continue
        time.sleep(a.delay); r = check(cat)
        with a.out.open("a") as f: f.write(json.dumps(r) + "\n")
        print(r["catalog"], r.get("http"), "exists" if r.get("exists") else "-", "disc" if r.get("discontinued") else "", flush=True)


if __name__ == "__main__":
    main()

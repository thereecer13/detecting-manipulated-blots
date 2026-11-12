"""Extract every image entry (catalog, image URL, application code, description) from cached Thermo
antibody product pages (the 'media-items' gallery data), for finding control images.

    python pilot/thermo_media.py <cache dir> --out media.jsonl
"""
import argparse, html, json, re
from pathlib import Path

ITEM = re.compile(r"\{'sku':'([^']+)','imageId':'(\d+)','imageUrl':'([^']+)'.*?'description':'((?:[^'\\]|\\.)*)'", re.S)


def items(text):
    for m in ITEM.finditer(text):
        sku, iid, url, desc = m.groups()
        url = url.replace("\\u003d", "=").split("?")[0]
        desc = html.unescape(desc.encode().decode("unicode_escape", "ignore")) if "\\" in desc else html.unescape(desc)
        app = re.search(r"-(WB|IF|ICC|IHC|IHC-P|IHC-F|IP|FC|Flow|ChIP|ELISA|IP|PLA|GS)[-_]", url.split("/")[-1])
        yield {"catalog": sku, "image_id": iid, "url": url, "app": app.group(1) if app else None, "description": desc}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cache", type=Path); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(); seen = set(); n = 0
    with a.out.open("w") as f:
        for p in a.cache.glob("*.html"):
            t = p.read_text(encoding="utf-8", errors="ignore")
            if "media-items" not in t: continue
            for it in items(t):
                k = (it["catalog"], it["image_id"])
                if k in seen: continue
                seen.add(k); f.write(json.dumps(it) + "\n"); n += 1
    print(n, "image entries from", len({k[0] for k in seen}), "products")


if __name__ == "__main__":
    main()

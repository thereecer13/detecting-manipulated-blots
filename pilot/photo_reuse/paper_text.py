"""Print the parts of a paper needed to argue why two panels should be different images.

Reads the article XML from the PMC open-data bucket (cached in --cache) and prints
  - the caption of each figure whose label matches --fig (e.g. "5" or "5|7"),
  - every main-text paragraph that cites one of those figures,
  - every paragraph (usually Methods) matching --grep (a regular expression).

    python3 paper_text.py PMC13079295 --fig 5 --grep "wound|incision|excis" --cache DIR
"""
import argparse, re, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import fetch_pmc_figures as F


def xml_of(pmcid, cache, delay=1.0):
    p = Path(cache) / f"{pmcid}.xml"
    if p.exists(): return p.read_text("utf-8", "replace")
    keys = re.findall(r"<Key>([^<]+)</Key>", F.get(f"{F.S3}/?list-type=2&prefix={pmcid}.&max-keys=200", delay).decode())
    xk = [k for k in keys if k.endswith(".xml")]
    if not xk: raise SystemExit("no XML in the open-data bucket for " + pmcid)
    x = F.get(f"{F.S3}/{urllib.parse.quote(xk[0])}", delay).decode("utf-8", "replace")
    Path(cache).mkdir(parents=True, exist_ok=True); p.write_text(x, "utf-8")
    return x


def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").strip()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("pmcid"); ap.add_argument("--fig", default=""); ap.add_argument("--grep", default="")
    ap.add_argument("--cache", required=True); ap.add_argument("--max", type=int, default=1200)
    a = ap.parse_args(); x = xml_of(a.pmcid, a.cache)
    figs = {}
    for m in re.finditer(r"<fig[ >].*?</fig>", x, re.S):
        blk = m.group(0); fid = re.search(r'id="([^"]+)"', blk); lab = clean(" ".join(re.findall(r"<label[ >].*?</label>", blk, re.S)))
        figs[fid.group(1) if fid else lab] = (lab, clean(" ".join(re.findall(r"<caption[ >].*?</caption>", blk, re.S))))
    want = [k for k, (lab, _) in figs.items() if a.fig and re.search(r"(?<!\d)(%s)(?!\d)" % a.fig, lab)]
    for k in want: print(f"== CAPTION {figs[k][0]}: {figs[k][1]}\n")
    body = re.sub(r"<fig[ >].*?</fig>", " ", x, flags=re.S)
    for m in re.finditer(r"<p[ >].*?</p>", body, re.S):
        para = m.group(0); t = clean(para)
        cites = any(re.search(r'rid="%s"' % re.escape(k), para) for k in want)
        hit = bool(a.grep) and re.search(a.grep, t, re.I)
        if cites or hit: print(("-- TEXT citing figure: " if cites else "-- TEXT matching: ") + t[:a.max] + "\n")

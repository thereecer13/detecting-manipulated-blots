"""Colony-plate reuse search at scale, one paper at a time, keeping almost nothing on disk.

For each sampled open-access paper: list its files in PMC's open-data bucket, download the article XML,
pick the figures whose caption mentions a colony / clonogenic assay, download only those, run the plate
detector and matcher (plate_dupes), and delete the figures again unless the paper has a matching pair.
Papers come from the same shuffled Europe PMC result list as the pilot (seed 1), positions --start..--end,
and --exclude drops the pilot's papers explicitly. Resumable: one JSON line per finished paper.

    python3 scale_up.py --out DIR --start 0 --end 5000 --exclude PILOT/plan.json
"""
import argparse, json, random, re, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import fetch_pmc_figures as F
import plate_dupes as P
QUERY = '"colony formation assay"'
def colony_figs(xml):
    out = []
    for m in re.finditer(r"<fig[ >].*?</fig>", xml, re.S):
        blk = m.group(0); cap = re.sub(r"<[^>]+>", " ", " ".join(re.findall(r"<(?:label|caption)[ >].*?</(?:label|caption)>", blk, re.S)))
        cap = re.sub(r"\s+", " ", cap).strip()
        if not re.search(r"colony|clonogenic", cap, re.I): continue
        for h in re.findall(r'<graphic[^>]*xlink:href="([^"]+)"', blk): out.append((h.split("/")[-1], cap))
    return out
def listing(pool, delay, out):
    """Europe PMC search listing, page by page, with retries; pages are cached so a restart continues."""
    import time
    q = urllib.parse.quote(f"({QUERY}) AND OPEN_ACCESS:Y AND HAS_FT:Y"); cf = out / "listing.json"
    st = json.loads(cf.read_text()) if cf.exists() else {"ids": [], "cursor": "*"}
    while len(st["ids"]) < pool and st["cursor"]:
        for attempt in range(6):
            try:
                d = json.loads(F.get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize=1000&resultType=lite&cursorMark={urllib.parse.quote(st['cursor'])}", delay)); break
            except Exception as e:
                print("listing retry", attempt, str(e)[:60], flush=True); time.sleep(30 * (attempt + 1))
        else: raise SystemExit("listing failed")
        st["ids"] += [(r["pmcid"], r.get("title"), r.get("journalTitle"), r.get("pubYear"), r.get("doi")) for r in d["resultList"]["result"] if r.get("pmcid")]
        nxt = d.get("nextCursorMark"); st["cursor"] = None if nxt in (None, st["cursor"]) else nxt
        cf.write_text(json.dumps(st)); print("listing", len(st["ids"]), flush=True)
    return st["ids"][:pool]
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--start", type=int, default=500)
    ap.add_argument("--end", type=int, default=5500); ap.add_argument("--pool", type=int, default=20000); ap.add_argument("--delay", type=float, default=1.0); ap.add_argument("--exclude", help="plan.json of an earlier run; its papers are left out")
    a = ap.parse_args(); (a.out / "figs").mkdir(parents=True, exist_ok=True); plan_f = a.out / "plan_all.json"
    if plan_f.exists(): ids = json.loads(plan_f.read_text())
    else:
        ids = listing(a.pool, a.delay, a.out); random.Random(1).shuffle(ids)
        skip = {x[0] for x in json.loads(Path(a.exclude).read_text())} if a.exclude else set()
        ids = [x for x in ids if x[0] not in skip]; plan_f.write_text(json.dumps(ids))
    res_f = a.out / "papers.jsonl"; done = {json.loads(l)["pmcid"] for l in res_f.open()} if res_f.exists() else set()
    for i, (pmcid, title, journal, year, doi) in enumerate(ids[a.start:a.end], a.start):
        if pmcid in done: continue
        rec = {"pmcid": pmcid, "title": title, "journal": journal, "year": year, "doi": doi, "figs": [], "plates": 0, "hits": []}
        try:
            keys = re.findall(r"<Key>([^<]+)</Key>", F.get(f"{F.S3}/?list-type=2&prefix={pmcid}.&max-keys=200", a.delay).decode())
            xk = [k for k in keys if k.endswith(".xml")]
            if xk:
                xml = F.get(f"{F.S3}/{urllib.parse.quote(xk[0])}", a.delay).decode("utf-8", "replace"); figs = []
                for href, cap in colony_figs(xml):
                    stem = re.sub(r"\.(jpg|jpeg|png|gif|tif|tiff)$", "", href, flags=re.I)
                    k = next((k for k in keys if re.search(r"\.(jpg|jpeg|png)$", k, re.I) and Path(k).stem == stem), None)
                    if not k: continue
                    p = a.out / "figs" / f"{pmcid}_{Path(k).name}"
                    if not p.exists(): p.write_bytes(F.get(f"{F.S3}/{urllib.parse.quote(k)}", a.delay))
                    figs.append({"pmcid": pmcid, "file": str(p), "caption": cap[:3000]})
                rec["figs"] = [{"file": Path(f["file"]).name, "caption": f["caption"]} for f in figs]
                if figs:
                    n, hits = P._paper(figs); rec["plates"] = n; rec["hits"] = hits
                    if not hits:
                        for f in figs: Path(f["file"]).unlink(missing_ok=True)
        except Exception as e:
            rec["error"] = str(e)[:120]
        with res_f.open("a") as fh: fh.write(json.dumps(rec) + "\n")
        print(f"[{i + 1}] {pmcid} figs {len(rec['figs'])} plates {rec['plates']} hits {len(rec['hits'])} {rec.get('error', '')}", flush=True)

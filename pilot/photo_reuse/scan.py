"""Photo reuse search over PMC open-access papers, one paper at a time (same pattern as colony/scale_up.py).

Papers come from a shuffled Europe PMC search (seed 1). For each paper: read the article XML from the
PMC open-data bucket, download only the figures whose caption matches the topic, run photo_dupes, and
delete the figures again unless the paper has a hit. Resumable: one JSON line per finished paper.

    python3 scan.py --topic bli  --out DIR --start 0 --end 300
    python3 scan.py --topic cell --out DIR --start 0 --end 300
"""
import argparse, json, random, re, sys, time, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent)); sys.path.insert(0, str(Path(__file__).parent))
import fetch_pmc_figures as F
import photo_dupes as P

TOPICS = {
    # query for the Europe PMC search, caption pattern, keep dark-background regions?
    "bli": ('"bioluminescence imaging" AND (mice OR mouse)',
            r"bioluminescen|IVIS|luciferase|in vivo imaging|luminescence", True),
    "cell": ('"wound healing assay" OR "scratch assay" OR "transwell assay"',
             r"wound|scratch|transwell|migrat|invasi|morpholog|bright.?field|phase.contrast", False),
}


def topic_figs(xml, pat):
    out = []
    for m in re.finditer(r"<fig[ >].*?</fig>", xml, re.S):
        blk = m.group(0)
        cap = re.sub(r"<[^>]+>", " ", " ".join(re.findall(r"<(?:label|caption)[ >].*?</(?:label|caption)>", blk, re.S)))
        cap = re.sub(r"\s+", " ", cap).strip()
        if not re.search(pat, cap, re.I): continue
        for h in re.findall(r'<graphic[^>]*xlink:href="([^"]+)"', blk): out.append((h.split("/")[-1], cap))
    return out


def listing(query, pool, delay, out):
    q = urllib.parse.quote(f"({query}) AND OPEN_ACCESS:Y AND HAS_FT:Y"); cf = out / "listing.json"
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
    ap = argparse.ArgumentParser(); ap.add_argument("--topic", choices=TOPICS, required=True); ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--start", type=int, default=0); ap.add_argument("--end", type=int, default=300)
    ap.add_argument("--pool", type=int, default=20000); ap.add_argument("--delay", type=float, default=1.0)
    a = ap.parse_args(); query, pat, dark = TOPICS[a.topic]
    (a.out / "figs").mkdir(parents=True, exist_ok=True); plan_f = a.out / "plan_all.json"
    if plan_f.exists(): ids = json.loads(plan_f.read_text())
    else:
        ids = listing(query, a.pool, a.delay, a.out); random.Random(1).shuffle(ids); plan_f.write_text(json.dumps(ids))
    res_f = a.out / "papers.jsonl"; done = {json.loads(l)["pmcid"] for l in res_f.open()} if res_f.exists() else set()
    for i, (pmcid, title, journal, year, doi) in enumerate(ids[a.start:a.end], a.start):
        if pmcid in done: continue
        rec = {"pmcid": pmcid, "title": title, "journal": journal, "year": year, "doi": doi, "figs": [], "area": 0, "hits": []}
        try:
            keys = re.findall(r"<Key>([^<]+)</Key>", F.get(f"{F.S3}/?list-type=2&prefix={pmcid}.&max-keys=200", a.delay).decode())
            xk = [k for k in keys if k.endswith(".xml")]
            if xk:
                xml = F.get(f"{F.S3}/{urllib.parse.quote(xk[0])}", a.delay).decode("utf-8", "replace"); files = []
                for href, cap in topic_figs(xml, pat):
                    stem = re.sub(r"\.(jpg|jpeg|png|gif|tif|tiff)$", "", href, flags=re.I)
                    k = next((k for k in keys if re.search(r"\.(jpg|jpeg|png)$", k, re.I) and Path(k).stem == stem), None)
                    if not k: continue
                    p = a.out / "figs" / f"{pmcid}_{Path(k).name}"
                    if not p.exists(): p.write_bytes(F.get(f"{F.S3}/{urllib.parse.quote(k)}", a.delay))
                    files.append(p); rec["figs"].append({"file": p.name, "caption": cap[:3000]})
                if files:
                    rec["area"], rec["hits"] = P.paper(files, dark)
                    if not rec["hits"]:
                        for p in files: p.unlink(missing_ok=True)
        except Exception as e:
            rec["error"] = str(e)[:120]
        with res_f.open("a") as fh: fh.write(json.dumps(rec) + "\n")
        print(f"[{i + 1}] {pmcid} figs {len(rec['figs'])} hits {len(rec['hits'])} {rec.get('error', '')}", flush=True)

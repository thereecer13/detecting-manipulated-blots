"""Find published papers that name given antibody catalog numbers, via the Europe PMC REST API.

For each catalog number: full-text phrase search, then for every hit with open full text, fetch the
XML and keep the sentences that contain the number (to confirm the match and see the application:
western blot, IHC, IF ...). Hits without open full text are kept with `context: null` (matched in
indexed text we could not read, so they need a manual check). One request per second.

    python pilot/find_citations.py PA5-99397 PA5-116113 ... --out citations.json
"""
import argparse, json, re, time, urllib.parse, urllib.request

API = "https://www.ebi.ac.uk/europepmc/webservices/rest"
UA = {"User-Agent": "antibody-citation-check/1.0 (academic research script)"}


def get(url, as_json=True):
    time.sleep(1.0)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        b = r.read()
    return json.loads(b) if as_json else b.decode("utf-8", "replace")


def search(cat):
    q = urllib.parse.quote(f'"{cat}"')
    out, cursor = [], "*"
    while True:
        d = get(f"{API}/search?query={q}&format=json&pageSize=100&resultType=core&cursorMark={urllib.parse.quote(cursor)}")
        out += d["resultList"]["result"]
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor or len(out) >= d["hitCount"]: return out
        cursor = nxt


def contexts(pmcid, cat):
    try: xml = get(f"{API}/{pmcid}/fullTextXML", as_json=False)
    except Exception: return None
    text = re.sub(r"<[^>]+>", " ", xml); text = re.sub(r"\s+", " ", text)
    num = cat.split("-")[1]
    pat = re.compile(rf"PA5[\s\-‐‑–_]*{num}(?!\d)")
    sents = []
    for m in pat.finditer(text):
        a = max(text.rfind(". ", 0, m.start()), m.start() - 300); b = text.find(". ", m.end()); b = len(text) if b < 0 else min(b + 1, m.end() + 300)
        sents.append(text[a + 1:b].strip())
    return sents


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("catalogs", nargs="+"); ap.add_argument("--out", required=True)
    a = ap.parse_args(); res = {}
    for cat in a.catalogs:
        hits = search(cat); res[cat] = []
        for h in hits:
            pmcid = h.get("pmcid")
            ctx = contexts(pmcid, cat) if pmcid and h.get("isOpenAccess") == "Y" or h.get("inEPMC") == "Y" else None
            res[cat].append({"title": h.get("title"), "journal": (h.get("journalInfo") or {}).get("journal", {}).get("title") or h.get("bookOrReportDetails", {}).get("publisher"),
                             "year": h.get("pubYear"), "doi": h.get("doi"), "pmid": h.get("pmid"), "pmcid": pmcid,
                             "source": h.get("source"), "authors": h.get("authorString"), "context": ctx})
        print(f"{cat}: {len(hits)} hits, {sum(1 for r in res[cat] if r['context'])} confirmed in full text", flush=True)
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()

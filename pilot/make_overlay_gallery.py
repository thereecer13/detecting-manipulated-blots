"""Self-contained HTML gallery of match_overlay.py outputs: for each pair, the flip GIF and the
orange match map, sorted by matched share, with an optional reference pair shown first.

    python pilot/make_overlay_gallery.py summary.jsonl jobs.txt out.html --title "..." [--reference prefix]

jobs.txt: tab-separated lines  A_path  B_path  out_prefix  label_A  label_B  (as fed to match_overlay.py)
"""
import argparse, base64, html, json
from collections import defaultdict
from pathlib import Path

CSS = """:root{--bg:#f6f6f4;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#ddddd8;--accent:#c96a00}
@media (prefers-color-scheme: dark){:root{--bg:#161615;--card:#1f1f1d;--ink:#ecece8;--muted:#a3a39c;--line:#34342f;--accent:#f0a040}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{padding:14px 16px;border-bottom:1px solid var(--line)}h1{font-size:18px;margin:0 0 4px}header p{margin:0;color:var(--muted);max-width:900px}
main{max-width:1400px;margin:0 auto;padding:16px;display:grid;gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card.ref{border:2px solid var(--accent)}.top{display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;margin-bottom:8px}
.top b{font-size:16px}.n{color:var(--muted)}.share{font-weight:600;color:var(--accent)}
.imgs{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}figure{margin:0;max-width:100%}
figure img{max-width:100%;height:auto;max-height:70vh;border:1px solid var(--line);border-radius:4px;background:#fff}
figcaption{font-size:13px;color:var(--muted)}"""


def uri(p, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(p).read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", type=Path); ap.add_argument("jobs", type=Path); ap.add_argument("out", type=Path)
    ap.add_argument("--title", required=True); ap.add_argument("--intro", default="")
    ap.add_argument("--reference", help="out_prefix of a reference pair to show first")
    a = ap.parse_args()
    summ = defaultdict(list)
    for l in a.summary.read_text().splitlines():
        d = json.loads(l); summ[(d["a"], d["b"])].append(d)
    rows = []
    for l in a.jobs.read_text().splitlines():
        A, B, o, la, lb = l.split("\t")
        d = summ[(la, lb)].pop(0) if summ[(la, lb)] else None
        if d is None or not Path(o + "_match.png").exists(): continue
        rows.append((o, la, lb, d))
    ref = [r for r in rows if r[0] == a.reference]; rest = sorted([r for r in rows if r[0] != a.reference], key=lambda r: -r[3]["match_share"])
    cards = []
    for i, (o, la, lb, d) in enumerate(ref + rest):
        is_ref = bool(ref) and i == 0
        tag = "Reference: a known true template pair" if is_ref else f"Candidate {i if ref else i + 1}"
        cards.append(f"""<section class="card{' ref' if is_ref else ''}"><div class="top"><span class="n">{html.escape(tag)}</span>
<b>{html.escape(la)} vs {html.escape(lb)}</b><span class="share">{d['match_share']:.0%} of shared background matches</span>
<span class="n">noise correlation {d['score']:.2f}, scale {d['scale']:.2f}</span></div><div class="imgs">
<figure><img loading="lazy" src="{uri(o + '_flip.gif', 'image/gif')}" alt="flip between the two aligned blots"><figcaption>Flips between the two blots, aligned and equalized. A shared background stays still while bands change.</figcaption></figure>
<figure><img loading="lazy" src="{uri(o + '_match.png', 'image/png')}" alt="match map"><figcaption>Orange: windows where the background noise of the two blots matches (local correlation above 0.5).</figcaption></figure>
</div></section>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(a.title)}</title><style>{CSS}</style></head><body><header><h1>{html.escape(a.title)}</h1><p>{html.escape(a.intro)}</p></header>
<main>{''.join(cards)}</main></body></html>"""
    a.out.write_text(page)
    print(f"wrote {a.out} ({a.out.stat().st_size / 1e6:.1f} MB, {len(cards)} pairs)")


if __name__ == "__main__":
    main()

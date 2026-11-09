"""Build a self-contained HTML review page: each item shows its images, a verdict dropdown and a notes
box. Progress is kept in the browser while reviewing; 'Export' downloads a JSON file to send back.

    python pilot/make_review_html.py items.json out.html --title "Clean vendor blots" \
        --choices "clean|manipulated|unsure|not a western blot"

items.json: [{"id": "...", "label": "shown above the item", "images": [{"path": "...", "caption": "..."}]}]
"""
import argparse, base64, html, io, json
from pathlib import Path
from PIL import Image


def data_uri(path, max_side=700):
    im = Image.open(path).convert("L")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{--bg:#f6f6f4;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#ddddd8;--accent:#2f5d8a;--ok:#2e7d4f;--bad:#b3402f;--warn:#a87511}
@media (prefers-color-scheme: dark){:root{--bg:#161615;--card:#1f1f1d;--ink:#ecece8;--muted:#a3a39c;--line:#34342f;--accent:#7aa7d6;--ok:#5fbf86;--bad:#e2806f;--warn:#d9b45a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
h1{font-size:17px;margin:0 12px 0 0}#progress{color:var(--muted)}
button,select{font:inherit;padding:6px 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--ink);cursor:pointer}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
main{max-width:1200px;margin:0 auto;padding:16px;display:grid;gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;border-left:5px solid var(--line)}
.card[data-v="__C0__"]{border-left-color:var(--ok)}.card[data-v="__C1__"]{border-left-color:var(--bad)}.card[data-v]:not([data-v=""]):not([data-v="__C0__"]):not([data-v="__C1__"]){border-left-color:var(--warn)}
.top{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px}.top b{font-size:16px}.n{color:var(--muted)}
.imgs{display:flex;flex-wrap:wrap;gap:10px}figure{margin:0;flex:1 1 280px;max-width:100%}
figure img{width:100%;height:auto;border:1px solid var(--line);border-radius:4px;background:#fff;cursor:zoom-in;image-rendering:auto}
figcaption{font-size:13px;color:var(--muted)}textarea{width:100%;min-height:44px;margin-top:10px;font:inherit;padding:6px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)}
#zoom{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:10;cursor:zoom-out}#zoom img{max-width:96vw;max-height:94vh;background:#fff}
</style></head><body>
<header><h1>__TITLE__</h1><span id="progress"></span>
<label>Show <select id="filter"><option value="all">all</option><option value="todo">not yet reviewed</option>__FILTER_OPTS__</select></label>
<button class="primary" id="export">Export results (.json)</button><button id="copy">Copy results</button></header>
<main id="list"></main><div id="zoom"><img alt="enlarged view"></div>
<script>
const ITEMS = __ITEMS__, CHOICES = __CHOICES__, KEY = "review:" + __REVIEW_ID__;
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { state = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
const list = document.getElementById("list"), progress = document.getElementById("progress"), filter = document.getElementById("filter");
function render() {
  list.innerHTML = "";
  ITEMS.forEach((it, i) => {
    const s = state[it.id] || {verdict: "", notes: ""};
    const f = filter.value;
    if (f === "todo" && s.verdict) return;
    if (f !== "all" && f !== "todo" && s.verdict !== f) return;
    const c = document.createElement("section"); c.className = "card"; c.dataset.v = s.verdict;
    c.innerHTML = `<div class="top"><span class="n">${i + 1}/${ITEMS.length}</span><b></b>
      <select aria-label="verdict"><option value="">— verdict —</option>${CHOICES.map(x => `<option>${x}</option>`).join("")}</select></div>
      <div class="imgs">${it.images.map(im => `<figure><img loading="lazy" src="${im.src}" alt=""><figcaption></figcaption></figure>`).join("")}</div>
      <textarea placeholder="Notes (optional): what you see, where"></textarea>`;
    c.querySelector("b").textContent = it.label;
    c.querySelectorAll("figcaption").forEach((fc, j) => fc.textContent = it.images[j].caption || "");
    c.querySelectorAll("figure img").forEach((img, j) => img.alt = it.label + " " + (it.images[j].caption || ""));
    const sel = c.querySelector("select"); sel.value = s.verdict;
    sel.onchange = () => { state[it.id] = {...(state[it.id] || {notes: ""}), verdict: sel.value}; c.dataset.v = sel.value; save(); count(); };
    const ta = c.querySelector("textarea"); ta.value = s.notes;
    ta.oninput = () => { state[it.id] = {...(state[it.id] || {verdict: ""}), notes: ta.value}; save(); };
    list.appendChild(c);
  });
  count();
}
function count() { const n = ITEMS.filter(it => (state[it.id] || {}).verdict).length; progress.textContent = `${n} of ${ITEMS.length} reviewed`; }
function results() { return JSON.stringify({review: __REVIEW_ID__, exported: new Date().toISOString(),
  items: ITEMS.map(it => ({id: it.id, label: it.label, verdict: (state[it.id] || {}).verdict || "", notes: (state[it.id] || {}).notes || ""}))}, null, 1); }
document.getElementById("export").onclick = () => { const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([results()], {type: "application/json"})); a.download = __REVIEW_ID__ + "_results.json"; a.click(); };
document.getElementById("copy").onclick = async () => { try { await navigator.clipboard.writeText(results()); alert("Copied. Paste it into the chat."); } catch (e) { alert("Copy failed; use Export instead."); } };
filter.onchange = render;
const zoom = document.getElementById("zoom");
list.addEventListener("click", e => { if (e.target.tagName === "IMG") { zoom.firstElementChild.src = e.target.src; zoom.style.display = "flex"; } });
zoom.onclick = () => zoom.style.display = "none";
render();
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", type=Path); ap.add_argument("out", type=Path)
    ap.add_argument("--title", required=True); ap.add_argument("--choices", required=True, help="'|'-separated; the first two get green/red")
    a = ap.parse_args()
    items = json.loads(a.items.read_text())
    for it in items:
        for im in it["images"]: im["src"] = data_uri(im.pop("path"))
    choices = a.choices.split("|")
    review_id = a.out.stem
    page = (PAGE.replace("__TITLE__", html.escape(a.title)).replace("__C0__", html.escape(choices[0])).replace("__C1__", html.escape(choices[1]))
            .replace("__FILTER_OPTS__", "".join(f"<option>{html.escape(c)}</option>" for c in choices))
            .replace("__CHOICES__", json.dumps(choices)).replace("__REVIEW_ID__", json.dumps(review_id))
            .replace("__ITEMS__", json.dumps(items)))
    a.out.write_text(page)
    print(f"wrote {a.out} ({a.out.stat().st_size / 1e6:.1f} MB, {len(items)} items)")


if __name__ == "__main__":
    main()

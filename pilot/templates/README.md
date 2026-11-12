# Hunting Richardson background templates in unflagged vendor products (pilot)

Scrape: `scrape_vendors.py --all-images --ranges ...` over unflagged Thermo Fisher products in the
catalog blocks where Richardson's template members cluster (PA5-99000-104999 and 114000-116999 for
patterns A/B; MA5-15xxx, 17xxx, 31xxx, 38xxx for C/D): 500 products, 702 western blot images.

Matcher: `template_match.py` (validation numbers in its docstring). 31 images scored >= 0.4.

First look (top 6 by score):
- PA5-99275 (Gastrin) vs pattern B (PA5-102533): **not a template member (corrected).** It was first
  reported as one because whole-figure noise correlation was 0.56-0.93. That correlation comes from
  the shared Thermo figure frame (box outline, ladder, lane numbers, arrow position), not the
  background. Strictly inside the lane, its grain does not match (correlation 0.06, median local
  window correlation 0.02), while true pattern B members match each other there (0.38-0.56 overall,
  local medians 0.64-0.96). Lesson: verify inside the blot lane only, away from frame lines; the
  window-by-window match map (`match_overlay.py`) does this.
- 4 are knockdown figures (blot + bar chart) where the largest "panel" is the chart: false.
- 1 (MA5-15084, phospho-PDGFRb) has nothing in common with its exemplar: false.

All 31 candidates checked with `match_overlay.py` (aligned at whole-pixel precision, window-by-
window noise correlation inside the blot panels). Reference: two known pattern B members
(PA5-102779 vs PA5-102533) match on 82% of their shared background (correlation 0.98); only the
patch around each figure's band differs. Candidates: highest 7% (PA5-99275, shared figure frame),
the rest 0-5%. **No new template member in this pilot.** The detector's hits were figure-layout
matches (Thermo uses the same frame, ladder and arrow positions for many products) or
wrong-panel comparisons (knockdown figures with bar charts).

Implication: the detector's validation recall (69%) was probably helped by template members also
sharing a figure frame. A better detector should score only the lane interior, as the overlay
map does, before a larger scan. `scan_scores.json` has every scraped image's best score, pattern and
exemplar.

## Detector v2 scan of the full PA5 template ranges

Scope: every unflagged Thermo PA5 product in catalog ranges PA5-99000 to 104999 and 114000 to 116999
(4,384 products, 4,337 with western blot images, 5,851 images), scraped politely. `template_scan2.py scan`
then `match_overlay.py` for each candidate at share 0.15 or higher, against three Richardson members of
its pattern (B: PA5-101612, PA5-102533, PA5-101939; A: PA5-102052, PA5-101544, PA5-102226). None of
these catalogs is in Richardson's June or August spreadsheets. All pattern-B hits share the 1.36 figure
aspect, and all but VEGFB come from one upload batch (image file names stamped 2019-08-08).

| Tier | Catalog | Target | Pattern | Matched share vs 3 members |
|---|---|---|---|---|
| confirmed | PA5-99397 | IL-5 | B | 73-82% |
| confirmed | PA5-99460 | Gastrin | B | 64-73% |
| confirmed | PA5-99462 | CDKN2C | B | 60-76% |
| confirmed | PA5-116113 | VEGFB | B | 64-75% |
| confirmed | PA5-99455 | PIASy | B | 44-80% |
| confirmed | PA5-99429 | NOTCH2 (cleaved Ala1734) | B | 38-67% |
| confirmed | PA5-99468 | Cyclin C | B | 53-60% |
| confirmed | PA5-99414 | HOXB5 | B | 33-65% |
| confirmed | PA5-99210 | TBX10 | B | 41-52% |
| confirmed | PA5-116143 | ZDHHC7 | A | 26-61% (noise corr 0.97; checked by eye) |
| likely | PA5-99252 | ARMX3 | B | 36-49% |
| likely | PA5-99459 | Fra2 | B | 40-47% |
| likely | PA5-99163 | Cyclin G1 | B | 32-37% |
| partial | PA5-99249 | VPS72 | B | 27-40% |
| partial | PA5-99281 | ELOVL4 | B | 20-28% |
| partial | PA5-99307 | SIX6 | B | 24-27% |
| partial | PA5-99296 | SURF1 | B | 21-23% |
| partial | PA5-99306 | CTU1 | B | 19-24% |
| partial | PA5-99283 | HSPH1 | B | 15-20% |
| no match | PA5-101954, PA5-101963 | | B | 0% (shared frame only) |

Tiers: confirmed = 50% or more against at least two members; likely = above about 27% against all
three; partial = a consistent region matches (always the strip left of lane 1 plus the bottom of the
panel). In the likely and partial hits the matched regions have the same shape against every member,
and the area around the band never matches: that fits a shared template background whose middle was
redrawn, but it needs a human look. Frame-sharing negatives in validation reached 0.33 at most.
Pattern-A members are cropped differently from one another, so pattern-A shares vary more; ZDHHC7
matches PA5-102052 over the whole lane outside the band (band moved from ~40 to ~33 kDa).
Pattern-A recall of the detector is lower (validation 6/30), so pattern-A members are likely undercounted.

## Did Thermo pull the flagged PA5 products?

Method: Richardson's Thermo catalog numbers compared with Thermo's antibody sitemap (249,420 products,
fetched 2026-11-11), then the product status that each page carries (`pilot/check_discontinued.py`):
45 flagged products (30 absent from the sitemap, 15 present) and a baseline of 200 random unflagged
catalog numbers from the same PA5 ranges that are absent from the sitemap
(`thermo_status_sample.jsonl`, checked 2026-11-12).

- Absent from the sitemap means hidden from search (`searchStatus: false`), not deleted: the product
  page, its datasheet and its western blot image stay online. 29 of 30 sampled absent flagged
  products are marked "long-term unavailable", 1 discontinued. All 15 present ones are searchable.
- Flagged PA5 products in the template ranges: 1,111 of 2,694 hidden (41%; pattern A 889/2,046,
  pattern B 209/594). Flagged MA5: about 2% hidden.
- Unflagged PA5 products in the same ranges: an estimated 1,893 of 6,277 hidden (30%; 197 of 200
  sampled absent numbers are real products, 186 long-term unavailable, 11 discontinued).
- So flagged products are hidden more often (41% vs 30%), but most of the hiding is not specific to
  flagged products; it looks like a broad withdrawal of this PA5 line that includes them. None of
  this says why: products go unavailable for supply reasons too. The hidden products' template
  images are still served on their product pages.

## Pattern A, new detector (`pilot/pattern_a.py`)

The template detector found only 2 of 23 pattern-A members because its exemplars came from
Richardson's archive figures, which are cropped differently from one another. On Thermo's current
product images, pattern-A figures use one layout (650 x 650 px, a single lane boxed at x = 194-300), so
lane interiors line up to within a few pixels. The new detector compares the grain inside the lane
(band masked; column / row streaks removed) at the best whole-pixel shift and counts the share of
31 x 31 windows that correlate. The match is the grain itself: aligned correlation 0.66 (median of
231 member pairs) drops below 0.12 when the lanes are shifted by 8 px.

- Validation, leave-one-out over the Thermo images of 23 Richardson pattern-A members: **23 of 23
  products detected** (window share 0.67-1.0). Not detected: PA5-114955's second image, a different
  2024 blot (arrow, lane number) that is not the template figure.
- 5,851 unflagged PA5 blots in the template ranges: 4 hits, highest other image 0.10.

| Catalog | Target | Window share | Notes |
|---|---|---|---|
| PA5-116129 | WNT5B | 1.0 | new, not in Richardson's spreadsheets or image archives |
| PA5-116130 | WNT9B | 1.0 | new |
| PA5-116125 | Wnt10B | 1.0 | new |
| PA5-116143 | ZDHHC7 | 0.75 | already found by the template detector (650 x 1020 figure, grey lane borders) |

Look-alikes rejected: boxes spanning several lanes or white gaps, and lanes with strong structure
inside the box (grain outside 1-8 gray levels). Limits: needs a boxed single lane; pattern-A figures in
other layouts (multi-lane) are not covered.

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

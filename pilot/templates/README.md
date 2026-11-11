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

## Detector v2 scan, interim (2,201 of the PA5 images scraped so far)

`template_scan2.py scan` on images from 1,475 of 4,500 PA5 products in the template catalog ranges,
then `match_overlay.py` against three Richardson pattern-B members (PA5-101612, PA5-102533 and
PA5-101939 or PA5-115761). None of these catalogs is in Richardson's June or August spreadsheets.
Every hit is pattern B, 1.36 figure aspect, and all but one come from the same 2019-08-08 upload batch.

| Tier | Catalog | Target | Matched share vs 3 members |
|---|---|---|---|
| confirmed | PA5-99397 | IL-5 | 73-82% |
| confirmed | PA5-116113 | VEGFB | 64-75% |
| confirmed | PA5-99210 | TBX10 | 41-52% |
| likely | PA5-99252 | ARMX3 | 36-49% |
| likely | PA5-99459 | Fra2 | 40-47% |
| partial | PA5-99249 | VPS72 | 27-40% |
| partial | PA5-99307 | SIX6 | 24-27% |
| partial | PA5-99296 | SURF1 | 21-23% |
| partial | PA5-99283 | HSPH1 | 15-20% |
| no match | PA5-101954, PA5-101963 | | 0% (shared frame only) |

Tiers: confirmed = 50% or more against at least two members; likely = above about 27% against all
three; partial = a consistent region matches (always the strip left of lane 1 plus the bottom of the
panel). In the likely and partial hits the matched regions have the same shape against every member,
and the area around the band never matches. That fits a shared template background whose middle was
redrawn, but it needs a human look. Frame-sharing negatives in validation reached 0.33 at most.

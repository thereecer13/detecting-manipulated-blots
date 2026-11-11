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

The remaining candidates are under review by the biologist (`template_candidates.html`, not
committed: vendor images). `scan_scores.json` has every scraped image's best score, pattern and
exemplar.

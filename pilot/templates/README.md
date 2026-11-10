# Hunting Richardson background templates in unflagged vendor products (pilot)

Scrape: `scrape_vendors.py --all-images --ranges ...` over unflagged Thermo Fisher products in the
catalog blocks where Richardson's template members cluster (PA5-99000-104999 and 114000-116999 for
patterns A/B; MA5-15xxx, 17xxx, 31xxx, 38xxx for C/D): 500 products, 702 western blot images.

Matcher: `template_match.py` (validation numbers in its docstring). 31 images scored >= 0.4.

First look (top 6 by score):
- PA5-99275 (Gastrin) shares the pattern B background: native noise correlation 0.56 with
  PA5-102533 (MSMB) and 0.58 / 0.33 with the other two same-size pattern B images. Not in
  Richardson's spreadsheet. **New template member.**
- 4 are knockdown figures (blot + bar chart) where the largest "panel" is the chart: false.
- 1 (MA5-15084, phospho-PDGFRb) has nothing in common with its exemplar: false.

The remaining candidates are under review by the biologist (`template_candidates.html`, not
committed: vendor images). `scan_scores.json` has every scraped image's best score, pattern and
exemplar.

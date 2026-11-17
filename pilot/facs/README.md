# Flow cytometry (FACS) duplication pilot

Sources
- BioFors (Sabir et al., ICCV 2021): 1,061 FACS panels with 82 labelled duplicate pairs, used to test the matcher.
- PMC Open Access subset (public cloud bucket): `fetch_pmc.py` finds papers whose figure captions mention flow
  cytometry and downloads those figures. First run: 1,000 papers (2019-2024), 1,980 figures.

What counts as a flow plot (`facs_panels.py`)
- a framed panel: nearly complete axis lines on the left and bottom, 60-700 px, roughly square;
- drawn on white (at least 45% near-white pixels), which removes photographs and heat maps;
- at least 30 isolated single dots that do not form a regular lattice (removes hatched bars);
- at least one of: a gate inside the frame (quadrant lines, rectangle or polygon) or logarithmic tick marks
  (gaps shrinking within a decade, at least two decades);
- frames that contain other frames are treated as containers, not plots.
Log ticks are rarely resolvable at the figure sizes PMC serves, so in practice the gate test decides.
First run: 958 flow panels in 398 of the 1,980 figures; a random sample of 80 was about 95% flow plots.

Matching (`panelmatch.py: dots, match_dots`)
- isolated dots (single events) of two panels are aligned by translation at a few scales; the score is the
  number of coinciding dots above the best chance alignment.
- BioFors: 22 of the top 25 and 40 of the top 50 of 8,222 candidate pairs are labelled duplicates
  (average precision 0.61); 58 of the 82 labelled pairs are found.

Review pages
- v1 (`figscan.py`, `build_review.py`): whole-figure autocorrelation; superseded, many hits were not flow plots.
- v2 (`facs_panels.py`, `build_review2.py`): panel pairs within one figure; 20 figures have a pair scoring >= 8.

Not covered yet: mirrored panels, histograms, pairs across figures or papers, cloned patches inside one plot.

Review of v2 (`review2_results.json`, key `review2_key.json`; 19 panel pairs)
- 6 duplicated, 1 unsure, 1 same data shown twice on purpose, 1 not a flow plot, 10 not duplicated.
- Coinciding dots minus the best chance alignment (M - S) separates them: duplicated 25-291, not duplicated
  9-17; the deliberate repeat scored 37, the unsure item 43 and the non-flow item 17. Working threshold: 20.
- `build_review2.py` now rings every coinciding dot and outlines the region they cover.

Within one plot (`within.py`): the same repeated-dot search inside each of the 958 flow panels found nothing
above chance (7 panels with 15-18 repeated dots, none convincing by eye).

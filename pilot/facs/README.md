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

Across figures of one paper (`cross_fig.py`, `build_review3.py`, key `review3_key.json`)
- Only figures whose caption mentions flow cytometry were fetched, so this covers 70 papers with detected
  flow plots in two or more such figures; supplementary figures are not included.
- 5 pairs score >= 8, in 2 papers: four pairs between Fig. 2 and Fig. 3 of PMC13488854 (plots drawn at
  different sizes), and one in PMC11896295 that is a grid of small plots matched on tick marks and labels
  (false by eye).

Review of the across-figure page (`review3_results.json`, key `review3_key.json`; 5 pairs)
- 4 duplicated (all in PMC13488854, Adv Rheumatol 2024, doi:10.1186/s42358-024-00427-2), 1 unsure (PMC11895658).
- The four PMC13488854 pairs are two panels of Fig. 2F against two panels of Fig. 3E: the "Control" and
  "IL-1β+si-Hck#2" apoptosis plots of each figure. Every one of the four combinations shares dots, so the
  overlap is not only the same condition shown again in a later figure: the Control plot of one figure also
  shares dots with the si-Hck#2 plot of the other. The quadrant percentages printed on the plots differ
  between the figures (e.g. Control Q1-LL 93.33% in Fig. 2, 92.48% in Fig. 3).
- Scores (coinciding dots minus best chance alignment) are 12 to 28, lower than most within-figure
  duplicates, because Fig. 3 is drawn at 80% of the size of Fig. 2.

## Scale-up: 9,000 more papers (`run_chunks.sh`)

Same search and source, results 1,001 to 10,000, in chunks of 1,000: fetch, `facs_panels.py`, `cross_fig.py`,
`within2.py`, then delete figures without a flow panel. 8,999 papers, 18,234 figures, 6,507 flow panels in
3,021 figures.

- Within one figure: 20 panel pairs in 15 figures score >= 20 (coinciding dots minus best chance alignment);
  25 more score 12 to 19 and were not reviewed.
- Across figures of one paper: 3 pairs score >= 20, 12 score >= 12, in 6 papers.
- Within one plot: 79 hits, the 16 highest checked by eye, none convincing. They are histograms, line charts,
  tables and grids of small plots that passed the flow-plot filter, and one dot plot with a weak overlap of
  neighbouring regions.

Pre-screen by eye and caption, before human review (`review4_key.json`; page of 15 items, ids F.. within a
figure and A.. across figures):
- look like one plot shown for two conditions: PMC11344568 Fig. 4 (different quadrant percentages),
  PMC11717013, PMC11665346 Fig. 5 (PRPS2-Flag vs siRNA-PRPS2), PMC11387078 (two plots with identical
  percentages), PMC11363581 Fig. 3 vs Fig. 5 (near-identical plots with slightly different percentages);
- probably deliberate: a plot next to its enlarged inset (PMC11098111, PMC11811720), a plot repeated with
  a gate drawn (PMC11564698), sequential gating (PMC11708019), the same gating plot in several figures
  (PMC11486373), the same contour plots with the same numbers in Fig. 3 and Fig. 4 (PMC11098115);
- not a flow plot: PMC11598135 (one correlation scatter shown twice with identical statistics);
- weak: PMC11420794 Fig. 1 vs Fig. 2.
Left off the page: a grid of small plots matched on frames (PMC11693865), one embedding map coloured by two
markers (PMC11402138), one false across-figure pair (PMC11658681) and six further pairs of PMC11098115.

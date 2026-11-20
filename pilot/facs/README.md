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

Labels for the scale-up page (`review4_results.json`, 15 items): 6 duplicated (PMC11344568, PMC11717013,
PMC11564698, PMC11387078, PMC11665346; PMC11420794 Fig. 1 vs Fig. 2), 5 not duplicated, 4 same data shown
twice on purpose. Two "not duplicated" items were one plot next to its own enlarged crop (PMC11098111,
PMC11811720).

Changes after that review
- GIFs: both plots are now cut at their own frame and brought to one size, so the frames coincide
  (`build_review2.py`). Before, the second plot was shifted to make the dots coincide.
- One plot cropped differently (`context.py`, used by `build_review2.py`): after aligning on the matching
  dots, if nearly all ink in the overlap agrees (>= 0.75) but the two frames do not coincide, the pair is one
  plot seen through two windows and is dropped. On all labelled pairs it flags four, all labelled not
  duplicated or unsure, and none of the 16 labelled duplicated.
- Labels: `context.py` also compares the title strip above the plots and the text printed inside them. This
  does not separate deliberate repeats from duplications (matching titles and numbers occur in both
  classes), so labels and workflow are read by eye for each candidate and written into the item's label.
- Lower scores: the 11 remaining figures with a pair scoring 12 to 19 were read by eye. Two are candidates
  (PMC11408713, Der p1+NC vs Der p1+shHDAC4; PMC11573321, Model vs TG; `review5_key.json`, labels pending),
  three are deliberate (one parent plot with two gates; one plot in two colourings; a preprint copy of a
  sequential-gating figure) and six are false matches on dotted grid lines, tick marks, dashed gate outlines
  or correlation matrices.

Mirrored and rotated matches (`flip_search.py`): every panel against itself and every pair of panels in a
figure, under left-right mirror, top-bottom flip and rotation by 90, 180 and 270 degrees; 7,367 panels in
3,393 figures. 25 hits (coinciding dots minus chance >= 12), all within one panel, none between panels.
The 16 best were checked by eye: dotted grids, symmetric curves, tables and bar charts, and eight real flow
plots whose coinciding dots are scattered through the plot at 12 to 18 above a chance level of 28 to 92.
None shows a compact mirrored or rotated patch.

Labels for the two lower-scoring candidates (`review5_results.json`): both not duplicated.

## Cloned patches inside dense regions (`patch_clone.py`, first version, not usable yet)

The dot matcher only sees isolated dots. `patch_clone.py` works on pixel texture instead: every 12 x 12
block position of a plot is indexed, textured blocks are compared with all others in four orientations, and
a clone is a set of blocks that match at one common offset (or one common mirror axis) and form a compact
region. Self-test on 60 real plots with one planted 26 to 44 px patch each, re-saved as JPEG: 26 of 60
planted clones found (same orientation 8 of 15, mirrored 4 of 15, flipped 7 of 15, rotated 7 of 15). The
clean plots are the problem: 57% produce some hit and the 95th percentile of their best score is higher
than most planted clones, because repeated glyphs (tick labels, percentages), tick marks and smooth
density-coloured regions match themselves. Next: mask text and ticks, require the matched region to lie in
the event cloud, and measure again before running it on the 7,367 plots.

`patch_clone.py`, second version: blocks touching printed text, the tick-mark margin (outer 6%) or frame
lines are dropped, and a block must be 8% to 85% ink. Same self-test: 15% of clean plots give a hit (was
57%; 90th percentile of the best clean score 10, 95th 22), but only 18 of 60 planted clones are found (was
26). Lowering the match threshold from 0.90 to 0.80 does not recover them, so the misses are probably
planted patches with too few textured blocks left after the masks. Not yet run on the real plots.

Why `patch_clone.py` misses planted clones: in a repeat of the self-test with the planted positions
recorded (40 plots), 11 were found. Every one of the 29 misses had fewer than 10% usable blocks inside the
planted patch (median 0%), where "usable" means textured, 8% to 85% ink and clear of text, ticks and lines;
both plots with at least 30% usable blocks were found. So the misses are not a matching failure: at the
size PMC serves, most of a plot, including much of the event cloud, has no texture the detector can use.
The detector is therefore run on the real plots as it is, as a search limited to their textured parts.

`patch_clone.py` on the real plots (7,367 panels in 3,393 figures): 950 panels give a hit (66 figures
errored), 316 with a score of 60 or more. The 20 highest were checked by eye and all are false: slanted
gate lines and polygon gates (only horizontal and vertical lines are masked), large printed digits that
repeat within a number ("55", "66"), dashed curves, tables, and a non-flow illustration. No cloned patch of
events among them. The detector is not usable as a screen in this state; it would need masks for lines at
any angle and for large text, and even then it only covers the textured share of a plot.

## Label check of the 16 confirmed pairs (18 Nov)
Shared dots mean the same recorded events; the plots can still be legitimate if the figure presents
them as the same sample (gating steps, a shared control). Each confirmed pair was read against its
panel labels and caption (`confirmed_key.json`, fields `bin` and `labels`):
- presented as different samples: 14 pairs (12 papers) - different treatment, dose, sort or donor group;
- unclear: 2 pairs (PMC13488854, the same group name in Fig. 2 and Fig. 3 with different percentages);
- same sample (legitimate): 0. Such pairs had already been labelled "same data shown twice on purpose"
  in the reviews.
Wording for the write-up: "the same events shown as two different samples", not "manipulated".

**Standing rule for every future FACS scan:** before a matching pair is reported or sent for review,
read the panel labels, row/column headers and caption, and sort it into one of the three bins above.
Only "different samples" and "unclear" pairs go forward; the bin and the labels read are recorded with
the pair.

## Within-plot clones: the old search was nearly blind; new detector (`within3.py`, 20 Nov)
Planted test of the old repeated-dot search (`figscan.scan`, as used by `within.py` / `within2.py`): a
rectangle of a real flow plot (18-35% of its width) pasted elsewhere in the same plot (darker pixel wins),
re-saved as JPEG 88. Found: 9 of 163. The earlier "nothing within plots" result therefore said little.

`within3.py`: mask of small ink blobs (single events; components over 30 px or wider than 8 px dropped,
outer 5% dropped), autocorrelation by FFT, spike at an offset = many dots coinciding with themselves at that
exact shift; z = excess over the local median of the autocorrelation. A hit must be at an oblique offset
(|dx|, |dy| > 4; horizontal and vertical offsets are text lines, ticks and stacked histograms), z >= 10, and
its coinciding dots must form one compact, non-linear cluster (>= 10 dots, >= 50% of all coinciding dots,
minor/major spread >= 0.2).
Planted test (`within3_plant_test.py`, 190 plots, patches 12-35% of the plot): passes for 26, and for 20 of
the 43 patches that contain at least 20 isolated dots; patches with fewer than 10 isolated dots are almost
never found. Clean plots passing: 0 of 190.
All 6,507 panels of the 9,000-paper scale-up: 14 panels pass, all false by eye (dotted or stepped gate
lines at an angle, repeated text labels, a dashed curve, dot-strip charts). No within-plot clone.
Limit: at PMC figure size most events merge into the cloud; only sparse regions with separate dots are
searchable.
Scale-up continued with `YEARS=2025:2026 TAG=y25_ run_chunks.sh` (48,135 papers match in 2025-2026,
44,529 in 2014-2018, 112,936 in 2019-2024 of which 10,000 are done).

### 2025-2026 batch 0 (1,000 papers, 20 Nov)
2,204 flow panels. Within-plot (`within3.py`): 2 panels pass the filter, both false by eye (a dotted
polygon-gate edge; a sparse two-colour cloud with 13 scattered coincidences).
Across figures: 1 pair, score 38 (136 coinciding dots, chance 72): PMC13769143 (Poult Sci 2026,
doi:10.1016/j.psj.2026.108081), Fig. 4D "PBS" and Fig. 6D "PBS". Same events by eye; the quadrant gates sit
at different positions and the percentages differ (3.13/0.27/5.53/6.21 vs 3.23/0.24/6.55/6.49).
Labels read (standing rule): both panels are the PBS-immunized group; Fig. 4D caption says PBMCs stimulated
with recombinant Mycoplasma antigen, Fig. 6D caption says SG-stimulated PBMCs. Bin: presented as different
samples (different stimulation), with the caveat that it is the control group in both. The JOL3193 and
JOL3203 panels of the two figures do not match. Not yet sent for review.

### 2025–2026 batches 1 and 2

2,054 and 2,155 panels (6,413 with batch 0). Within-plot filter passed
two panels, both false: a hex-binned trajectory plot and a ROC curve whose
legend text repeats (neither is a flow plot). Cross-figure pairs with score
>= 20, binned by labels and captions:

- PMC13167764 (PNAS 2026) Fig 4 and Fig 5, "Isotype" in both: same sample
  (the isotype control of one day-6 experiment), not reported.
- PMC13712078 (J Transl Med 2026) Fig 4 and Fig 5: the two figure files are
  the same image in full. The Fig 4 caption describes other panels
  (immunofluorescence, uptake), so the Fig 5 image was posted in the Fig 4
  slot. A wrong-file error, not a duplicated plot.

### 2025–2026 batches 3 and 4

2,230 and 2,226 panels (10,869 with batches 0–2). Within-plot filter passed
five panels, all false: matches on printed quadrant percentages or gate
outlines, a line chart and a scatter chart. One cross-figure pair with
score >= 20: PMC13638297 (Gut 2026) Fig 3G and Fig 4B, "anti-CD3" in both,
the shared unstimulated-comparison sample for two treatments; same sample,
not reported.

### 2025–2026 batch 5

2,417 panels (13,286 so far). Within-plot filter passed two panels, both
false (gate label text, a paired-dot bar chart). Cross-figure pairs:
PMC13539813, two image files that are both the paper's Fig. 3 (same label
and caption), not a duplication.

### 2025–2026 batches 6 and 7

2,396 and 748 panels (16,430 so far). Within-plot filter passed three
panels, all false (legend text on two histograms, a gate outline).
Cross-figure pairs, both same sample: PMC13524787 (Fig 3 plots repeated
in Extended Data Fig 3 as the gating example) and PMC13459713 (one
screen-enrichment plot with different genes highlighted).

### 2025–2026 batches 8 and 9, and the paging limit

716 and 807 panels (17,953 so far). Within-plot filter passed two panels,
both false (a violin plot, a bar chart with data points). No cross-figure
pairs with score >= 20.

The NCBI search cannot page past 10,000 results, so batch 10 came back
empty. `fetch_pmc.py` now reads a list of papers already done (`SEEN`
environment variable) and later runs use date windows of under 10,000
papers each (`YEARS=2025/10/01:2025/12/31 TAG=y25q4_`). Window sizes:
2025 Q1 6,188; Q2 6,102; Q3 6,624; Q4 6,848; 2026 22,372. The 9,998 done
so far are the first 10,000 of the combined 2025–2026 search.

### 2025 Q4 window, batches 0–2

528, 645 and 669 panels (19,795 so far). Within-plot filter passed four
panels, all false (a line chart, two scatter charts with fit lines, a
histogram legend). One cross-figure pair: PMC12902099 (Commun Biol 2025)
Fig 5A and Fig 9A, the Control and OGD/R JC-1 plots. Both figures list
Control and OGD/R as conditions, so this is a shared control, not
reported. Side note: the Control plot is printed with 97.52/2.47 in Fig 5
and 97.42/2.57 in Fig 9.

### 2025 Q4 window, batches 3–6 (window complete)

676, 609, 595 and 579 panels (22,254 so far). Within-plot filter passed
five panels, all false (a gene scatter with reference lines, histogram
and plot label text, a fitted-curve chart). Cross-figure pairs:
PMC12651925 Fig 9 and Fig 10, the same single-agent/control histogram in
two combination figures (same sample); PMC12632077, one figure stored
under two file names.

### 2025 Q3 window, batches 0–3

605, 687, 763 and 653 panels (24,962 so far). Within-plot filter passed
two panels, both false (a strip chart of points, a scatter chart with a
fit line). One cross-figure pair: PMC13283291 Fig 2 and Fig 5, the same
Live/Dead gating example in two gating-strategy panels (gating plot, not
reported).

### 2025 Q3 window, batches 4–6 (window complete)

643, 711 and 477 panels (26,793 so far). Within-plot filter passed five
panels, all false (three line charts with error bars, two enrichment
plots matched on their label text). No cross-figure pairs.

### 2025 Q2 window, batches 0–3

666, 674, 595 and 729 panels (29,457 so far). Within-plot filter passed
two panels, both false (plot label text, a dashed gate outline). One
cross-figure match: PMC12152194, where the files for Figure EV1 and
Figure 2 in the PMC package are byte-identical (one image stored under
two names, a deposit error rather than panel reuse).

### 2025 Q2 window, batches 4–6 (window complete)

665, 700 and 51 panels (30,873 so far). Within-plot filter passed four
panels, all false (gate label text, bar-chart P-value text). Cross-figure
matches were all file-level, not panel reuse: PMC12084385 and
PMC12081931 each store one byte-identical image under two figure names
(as PMC12152194 above, all three EMBO Press papers with EV figures);
PMC12090378 has two versions of its Fig. 3 in the package (same flow
plots, one microscopy panel differs), likely a correction.

Paused here at 1.5 GB free disk; 2025 Q1 and the 2026 windows remain.

### 2025 Q1 window, batches 0–3

Resumed after freeing disk (colony paper downloads deleted). 609, 766,
764 and 663 panels (33,675 so far). Within-plot filter passed seven
panels, all false (a gate outline, a schematic, line charts, legend and
label text). One cross-figure match: PMC11904033, again one
byte-identical image stored under two figure names (EMBO Press).

# Reused colony-assay plates in published papers

Detector: `pilot/plate_dupes.py` (Hough circles with a rim test; SIFT + similarity RANSAC, plain and
mirrored; pixel NCC). Validation: 296/300 rotated / mirrored / rescaled / re-compressed copies found,
0/291 plates from other papers matched.

Sample: 500 random open-access PMC papers matching `"colony formation assay"` (Europe PMC search,
figures from the PMC open-data bucket). 399 papers had figures whose caption mentions a colony /
clonogenic assay: 778 figures, 3,522 plates detected.

Detector output: 13 matching plate pairs in 9 papers. Checked by eye and with a red/green overlay
of the aligned plates (colonies of a reused plate overlap as yellow; the same plate rotated 90
degrees as a control gives red and green):

| Paper | Plates | Same image? | Notes |
|---|---|---|---|
| PMC11550297, Discov Oncol 2024, doi:10.1007/s12672-024-01496-x | Fig 4I: HCT116 SI-NC = SW480 SI-NC, and HCT116 SI-POLQ = SW480 SI-POLQ | yes (355 colonies aligned, NCC 0.99) | Whole SW480 row repeats the HCT116 row; two different cell lines. Bar charts 4J/4K report different counts. |
| PMC12813190, Front Pharmacol 2025, doi:10.3389/fphar.2025.1725886 | Fig 2M Ishikawa: vehicle 2.5 uM = NEK6-OE 5 uM | yes (overlay corr 0.78 vs 0.03 control) | Different genotype and dose. |
| PMC12442663, Adv Sci 2025, doi:10.1002/advs.202504688 | Fig 9L T24 "P.d CM" = Fig 10I T24 "300 uM" 3-IAA | yes (overlay corr 0.87 vs 0.02 control) | Different treatments in different figures; low resolution. |
| PMC11648741, Research 2024, doi:10.34133/research.0553 | Fig 1C Control = Fig 8B Control (MDA-MB-231) | yes, contrast/colour changed (overlay corr 0.60 vs -0.01) | Same condition in two experiments (DOX/ononin vs PMA/ononin); a shared control is possible but is not stated in the captions. |
| 5 other papers | | no | Axis labels, chart gridlines, bar hatching, gridded methylcellulose wells. |

So 4 of 399 papers (1%) contain a reused plate the detector can find. This is a lower bound: it
misses plates it cannot segment (square wells, plates cut by panel borders) and reuse across papers.
Not checked against PubPeer or published corrections yet.

Hit list (machine output): `hits_all.json` (paths are relative to the scratch download).

## Reviewer's verdicts (20 Nov, `review_results.json`)
| Paper | Verdict |
|---|---|
| PMC11550297 (HCT116 / SW480 rows) | same plate, shown as different samples |
| PMC12813190 (vehicle 2.5 uM / NEK6-OE 5 uM) | unsure: resolution too poor |
| PMC12442663 (Fig 9L / Fig 10I) | unsure: resolution too poor |
| PMC11648741 (Control in Fig 1C / Fig 8B) | same plate, legitimate: shared control |

Confirmed as a problem: 1 of 399 papers. Two more need the figures at higher resolution than the PMC copies.

### Update from the reviewer (20 Nov)
After checking the two low-resolution cases at the source, the reviewer confirms both:
- PMC12813190 (Front Pharmacol 2025, Fig 2M): same plate, shown as different samples.
- PMC12442663 (Adv Sci 2025, Fig 9L / Fig 10I): same plate; per the reviewer the issue has since been
  addressed and the authors replaced the plate with the correct one. (Correction notice not looked up or
  linked here yet.)
Final tally of the 500-paper pilot: 3 of 399 papers with a plate shown as different samples (one of them
already corrected by the authors), 1 legitimate shared control, 5 false matches. All three confirmed
cases were found from the PMC copies at about 40-45 px per plate.

## Scale-up to 5,000 papers (in progress)

First 902 papers (5,764 plates): 11 papers flagged. After viewing each
pair and reading labels and captions:

- 1 candidate, on review page round 2 (`review2_key.json`): PMC12336053,
  Fig 3C HCT116 Tianma 0.2 mg/mL and Fig 8D SW480 berberine 25 ug/mL.
- 3 same sample, not reported: PMC6111824 (NC, NCI-H1975 in Fig 1D and
  Fig 6A), PMC11680982 (shHER2 + ET + CDK4/6i in Fig 3 and Fig 6B),
  PMC12334625 (parental A204 dose rows in Fig 1B and Fig 2B).
- 1 same image file listed under two figure names (PMC12686467).
- 1 too low in resolution to judge (PMC11670111, two adjacent wells).
- 5 false: a drawn schematic, bar charts, transwell images, and sparse
  plates matched on their printed scale bars.

Round 2 verdict (`review2_results.json`): PMC12336053 confirmed as the same
plate shown as different samples. Confirmed so far: 4 (3 in the pilot of
399 papers, 1 in the first 902 of the scale-up).

Papers 903–1,969: 17 more papers flagged. 3 candidates on review page
round 3 (`review3_key.json`, built with `make_packet.py`): PMC6657265,
PMC11173063, PMC12036886. Same sample, not reported: PMC8124562 (0 Gy and
4 Gy plates repeated as the no-inhibitor controls of panel D), PMC8006274
(HT29 NC in Fig 2B and Fig 5B, weak match), PMC9273950 (plate reused as an
icon in the method schematic). False: bar charts, schematics, empty well
frames, tissue cores, and PMC8568022, where two image files of one split
figure both contain panel J.

Papers 1,970–2,768: 13 more papers flagged. 4 candidates on review page
round 4 (`review4_key.json`): PMC9937894, PMC11540088 (the first rotated
match, 89 degrees), PMC10470409, PMC10411479. Not reported: PMC12089262
(a plate next to its own colony-count overlay). False: bar charts, cartoon
plates and cells, a flow plot. `make_packet.py` now adds a turned or
mirrored copy of the left plate when the match is rotated or mirrored.

Papers 2,769–3,343: 10 more papers flagged. 3 candidates on review page
round 5 (`review5_key.json`): PMC12205545, PMC10912303, and PMC12876004
(transwell invasion images, not plates, matched across two cell lines).
Same sample, not reported: PMC12222551 (miR-141-3p mimic plates repeated
in the co-transfection figure), PMC13104100 (30 uM plate in panels a and
b). False: plates matched on their drawn inset frames, bar charts, CT
scans, a heatmap legend, cartoon plates.

Papers 3,344–4,001: 11 more papers flagged. 5 candidates on review page
round 6 (`review6_key.json`): PMC11392926, PMC8019231, PMC8215359,
PMC13088848, PMC9761148. Same sample, not reported: PMC12373508 (A549
L-Cys plate in Fig 1a and Extended Data Fig 1a), PMC12595022 (untreated
Control and MDMX plates reused as the baseline of later panels). False:
bar charts and mouse imaging panels.

### PMC10470409 Fig 7B, closer look (user-supplied high-resolution figure)

`compare_two_plates_PMC10470409.py` aligns the PC-3 shS+NPHP4 plate onto
the C4-2B one and lists colonies found in only one. Result: the top-edge
smear, the chain of colonies in the upper centre-right, the right-hand
cluster and the background streaks coincide; 17 colonies appear only in
the C4-2B plate and 19 only in the PC-3 plate, mostly in the left and
lower parts (pixel agreement 0.44 top, 0.22 bottom). The colony pattern
in the PC-3 plate is also 11% larger while the plate outline is the same
size. Reading: one plate image, enlarged and with colonies removed and
added, not a plain copy.

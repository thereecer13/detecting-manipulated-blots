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

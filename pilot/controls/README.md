# Reused "no primary antibody" control panels on Thermo Fisher antibody pages

Sample: 3,500 Thermo antibody product pages (stratified: PA5- 2,000, MA5- 1,000, other 500, seed 1;
`pilot/sample_controls.py`) plus 62 products cached earlier. Microscopy figures whose description
mentions a no-primary / secondary-only control: 176 figures from 155 products, split into 876 panels.
Every panel was compared with every panel of other products (`pilot/panel_dupes.py`, normalized
cross-correlation over scales 0.8-1.25). All pairs scoring >= 0.84 were checked by eye.

Confirmed: the same control panel on products for different antibodies (5 groups, 11 products):

| Products (target) | Image dates in file names | Notes |
|---|---|---|
| PA5-100535 (FZR1), PA5-89181 (BAF57) | both 2021-03-23 | unrelated targets |
| MA5-32482 (PKC delta), MA5-34812 (BRD2) | 2023-03 / 2022-11 | unrelated targets; the stained panels show different cell fields |
| PA5-17652 (RAN), PA5-22048 (RAG2), PA5-29233 (Cyclin B2) | 2020-01 / 2019-03 / 2018-11 | three unrelated targets; the panel is relabelled and rescaled |
| MA5-32771 (TXNIP), MA5-32252 (C/EBP beta) | 2025-07 / 2026-04 | unrelated targets |
| PA5-116926, PA5-115736 (both Pericentrin) | 2024-02 / 2024-04 | same target; could be one shared experiment |

False matches checked and rejected: dark, sparse panels (e.g. MA5-35079 vs 740054M), negative-cell
panels and DAPI-only panels that merely look alike.

Interpretation: a no-primary control shows the background of the secondary antibody in that cell
prep. A shared panel is only valid if the two antibodies were stained side by side in the same
experiment. The stained panels, dates and cell fields differ in most groups above, so the control
shown was not run alongside the antibody it is presented with.

Coverage: 11 of the 155 sampled products with a control figure (7%) share their control with
another sampled product. A pair is found only when both products are in the sample, so the
catalog-wide count is likely much higher.

Image URLs: `confirmed_pairs.json`.

## Full PA5/MA5 crawl (in progress): any panel shared between products

`pilot/crawl_icc.py` downloads every ICC/IF figure of every PA5- and MA5- product; `pilot/shared_panels.py`
compares every panel with every panel of other products, each level-stretched so near-black panels can
match. Bright pairs must also match in fine detail (high-pass NCC >= 0.55; true copies >= 0.70, cells-on-
black look-alikes <= 0.35). Pairs with a dark panel are matched on smoothed panels and checked by eye.

First batch (3,389 figures, 9,401 panels; the figures of earlier-crawled products):
- **PA5-115786 (PF4) and PA5-100429 (CCDC53): the whole figure is the same** (all four panels: red, green
  beta-tubulin, DAPI, merge; HeLa). Both descriptions give red as the product's own antibody. Images
  uploaded 2021-01-13 (PF4) and 2019-08-08 (CCDC53). Neither is in Richardson's spreadsheets.
- PA5-88731 and PA5-87186 (both LSM1): same image; same target, plausibly legitimate.
- The five groups above are found again.
- 28 product pairs involving a dark panel: all checked by eye, all false (lone nuclei / blobs on black,
  empty noise panels). No reused near-black control yet.

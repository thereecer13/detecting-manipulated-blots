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

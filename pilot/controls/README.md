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

Second batch (4,339 figures; adds the first ~1,500 crawled MA5 pages):
- **PA5-79444 (IGF1R) and MA5-14924 (Lyn): same "No Primary antibody" panel, but the IGF1R figure is
  MCF7 cells and the Lyn figure A431 cells.** One control cannot be from both cell lines. Both images
  stamped 2021-03-23 11:04:06 (the batch of the FZR1 / BAF57 pair).
- **MA5-31961 (HSP70) and MA5-24843 (HSPA4): the same HeLa image** (the HSPA4 one is a 150 x 124 copy);
  HSPA4 and HSP70 (HSPA1A) are different proteins.
- PA5-90290 (PRMT5) and MA5-41126 (LDHB): same no-primary panel, both HeLa, same upload stamp
  (2022-08-18); the stained panels show different fields. Possibly one shared experiment.
- MA5-48110 (CD35) and MA5-48112 (CD25): same isotype-control panel, both Jurkat, same upload stamp;
  plausibly one shared experiment.
- Same target or same protein (likely legitimate): JMJD1B MA5-14792 / MA5-44598, PTP1B MA5-25574 /
  MA5-25642, 14-3-3 eta MA5-24792 / MA5-47416, CD107b MA5-31970 = LAMP2 MA5-35052.
- 23 new pairs involving a dark panel: all false by eye.

Third batch (5,515 figures; crawl at ~4,450 MA5 pages):
- **IGF1R / Lyn group grows to three cell lines**: the same "No Primary antibody" panel is labelled MCF7
  (PA5-79444, IGF1R), A431 (MA5-14924, Lyn) and PC3 (MA5-15329, Lyn). All stamped 2021-03-23 11:04:06.
- **MA5-29441 (IkB alpha, HeLa, uploaded 2020-08-24) and MA5-24791 (EWSR1, MCF7, uploaded 2020-03-04):
  same no-primary panel**, different cell lines, six months apart; the control's elongated cells do not
  look like the clustered MCF7 cells in the EWSR1 panels.
- FZR1 / BAF57 group adds MA5-27318 (RRM2); all A-431, 2021-03-23 batch.
- MA5-24861 (ACLY) and MA5-15692 (ALDH1A1): same no-primary panel, both A549.
- 2022-08-18 batch, HeLa: PRMT5 (PA5-90290), LDHB (MA5-41126) and HNRNPC (MA5-32270) share one
  no-primary panel; VASP (MA5-38250) and LDLR (MA5-38556) share another. Possibly shared experiments.
- MA5-38184 (TRBP) and MA5-32246 (MyD88): same no-primary panel, HeLa, 2023-02-13 batch.
- Same target (likely legitimate): Pan-cadherin, HSPB8, GSTP, PP1A, Rb, CD30, TLE1, SMC1, ACLY, cardiac
  troponin T product pairs.
- Dark pairs: 109, of which 105 involve 15 "hub" panels (lone cells, blobs, empty noise) that loosely
  match many dark panels; the other 4 were false by eye. `shared_panels.py` now tags hub pairs.
- Blots of the same pages: template scan 70 hit products, 69 already in Richardson's lists, the other
  (MA5-32110, a six-lane ABCG1 blot) matched only a strip of the GAPDH panel edge: false. Pattern A: 0.

Fourth batch (6,083 figures; crawl at ~6,000 MA5 pages):
- **MA5-54064 (alpha-smooth muscle actin, human HT-1080 cells) and MA5-54052 (Arp2, mouse C2C12 cells):
  pixel-identical figures** (DAPI / antibody / merge strip; different files, same 2024-06-25 14:41:28
  stamp). This is the stained panel itself, not a control, captioned as two antibodies in two species.
- **MA5-32397 (CDK9, A-431) and MA5-25137 (KHK, U-87 MG): same no-primary panel**, different cell
  lines, both stamped 2021-03-23 11:04:06 (the FZR1 / BAF57 / IGF1R batch).
- ACLY / ALDH1A1 group adds MA5-29049 (Bcl-xL); all three captions say A549.
- 2022-08-18 HeLa group adds MA5-32690 (clathrin heavy chain): four products, one no-primary panel.
- Same target (likely legitimate): SQSTM1, cytokeratin 5, IGF2BP3, TEAD1 product pairs.
- Dark pairs: 9 new, 7 tagged hubs, 2 false by eye.
- Blots of the same pages (1,365 new): template scan 27 hit products, 26 already in Richardson's lists;
  the other (MA5-24785, RBP4, weak pattern-C score) fails the overlay check (7% match share): false.
  Pattern A: 0 hits (highest window share 0.09).

Fifth batch (6,740 figures; crawl at ~7,600 MA5 pages):
- **BeWo no-primary panel on four products across four months**: PKC delta (MA5-32482, stamped
  2023-03-16), BRD2 (MA5-34812, 2022-11-28), cIAP1 (MA5-35343, 2022-11-28) and PTGES2 (MA5-26128,
  2023-01-12). (PKC delta / BRD2 was found in the sample; two more products now.)
- **2022-08-18 HeLa panel (PRMT5 / LDHB / HNRNPC / CLTC) reappears on XPO1 (MA5-41253) and ADAR1
  (MA5-35112), both stamped 2022-11-28**: six products, one no-primary panel, two upload dates.
- **RAD54L2 PA5-99087 (2022-03-01) and Survivin MA5-15077 (2020-07-13): same no-primary panel**, HeLa,
  uploaded 20 months apart.
- MA5-48060 (galiximab) and MA5-48065 (CD40): same isotype-control panel, Daudi, same 2023-09-05 batch
  (one experiment's control shown on two products; lower concern).
- Same target (likely legitimate): MCM6, JMJD1B, M-CSF, S100A9, RhoGDI product pairs.
- Dark pairs: 41 new, 33 tagged hubs, the other 8 false by eye.
- Blots (1,379 new): template scan 37 hit products, 35 already in Richardson's lists; MA5-51464 fails the
  overlay check (0% match share); MA5-36069 (a blue single-lane blot) does not resemble its exemplar by eye.
  Pattern A: 0 hits (highest window share 0.14).

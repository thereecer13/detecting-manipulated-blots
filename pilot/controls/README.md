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

Sixth batch (7,305 figures; crawl at ~9,000 MA5 pages):
- **HeLa no-primary panel now on seven products**: SMARCC1 (MA5-34657, stamped 2022-10-10) joins
  PRMT5 / LDHB / HNRNPC / CLTC (2022-08-18) and XPO1 / ADAR1 (2022-11-28).
- **Prohibitin PA5-17325 (2020-08-24) and SDHA MA5-32598 (2020-07-13): same no-primary panel**, HeLa.
- IkB alpha / EWSR1 group adds a second IkB alpha product (MA5-15153, HeLa, same 2020-08-24 stamp as
  MA5-29441); the EWSR1 caption still says MCF7.
- SMAD2 MA5-41103 and Smad3 MA5-35269: same no-primary panel, A549, same 2024-10-29 batch, but different
  DAPI panels (one experiment's control on two related products; lower concern).
- Same target (likely legitimate): SHIP1, ALKBH, GCN2 product pairs.
- Dark pairs: 23 new, 22 tagged hubs, the other false by eye.
- Blots (1,328 new): template scan 45 hit products, all already in Richardson's lists. Pattern A: 0 hits.

Seventh batch (7,695 figures; crawl at ~10,000 MA5 pages):
- RAN / RAG2 / Cyclin B2 group (from the sample) adds Ku80 MA5-16375; all HeLa.
- EIF2S1 MA5-52465 and XIAP MA5-52464: same no-primary panel, HeLa, same 2024-07-02 batch (lower concern).
- Dark pairs: 21 new; 13 tagged hubs; the other 8 false by eye (5 involve MA5-14327, a new hub-like panel).
- **Blots: MR1 MA5-48493 (uploaded 2025-12-01, not in Richardson's lists) shares lane background with
  template members FLT3 MA5-38523 and MA5-38647** - see pilot/templates/README.md. MA5-44552 (lane-edge
  strip) and MA5-11869 (9% overlay) false. Pattern A: 0 hits.

Eighth batch (8,432 figures; crawl at ~11,800 MA5 pages):
- **SUMO1 MA5-14877 (stamped 2022-06-03) and BAK MA5-33215 (stamped 2026-01-06): same no-primary panel**,
  both A-431, uploaded three and a half years apart.
- **HEK 293 no-primary panel: PKC delta MA5-32482 (figure 3, 2023-03-16) and GLUT1 MA5-37843 (2022-08-18).**
- **A549 no-primary panel on MEKK2 MA5-37973 (2024-04-15), MYST1 MA5-34741 (2024-05-21) and Map3k2
  MA5-32237.**
- Neutrophil elastase MA5-32548 and STING MA5-26030: same no-primary panel, THP-1.
- HeLa group grows to nine products (second LDHB MA5-35655 and second SMARCC1 MA5-35475, the latter
  stamped 2022-09-26); Prohibitin / SDHA adds a second Prohibitin product (MA5-15899).
- Related or same target (likely legitimate): ATM / phospho-ATM (same experiment), MA5-15256 / MA5-13070
  (the same published Nature Communications figure), and EpCAM, KRT8, CA125, ENDOG, RBM3, pan-cytokeratin,
  MBD, HNRNPH1, LPL, TP53, PKM2, TOMM20, phospho-H2A product pairs.
- Dark pairs: 25 new; 15 tagged hubs; the other 10 false by eye.
- Blots (1,596 new): template scan 42 hit products, all already in Richardson's lists. Pattern A: 0 hits.

Ninth batch (9,002 figures; crawl at ~13,450 MA5/PA5 pages):
- **SMARCB1 PA5-53932 (stamped 2020-03-04) and ERG MA5-26261 (stamped 2019-12-09): same no-primary
  panel**, both HeLa. The two captions give different protocols (permeabilization 15 vs 10 minutes,
  blocking 1 hour vs 10 minutes), yet the control panel is identical.
- Same target (likely legitimate): HMGB1, EpCAM, Histone H3, DPYSL2, TSPO, alpha-ketoglutarate-dependent
  dioxygenase, MTDH, VPS35, RAB21, progesterone receptor, Rab9a, HMPV, desmin, ZFP36, GAPDH product pairs.
- Dark pairs: 10 new; 8 tagged hubs; the other 2 (MA5-41175 vs ERG MA5-26261) false by eye.
- Blots (1,414 new): template scan 32 hit products, all already in Richardson's lists. Pattern A: 0 hits.

Tenth batch (9,601 figures; crawl at ~14,900 MA5/PA5 pages):
- **HeLa group grows to ten products: SP1 MA5-35331 (figure 4, stamped 2022-08-18, the same day as the
  PRMT5 / LDHB / HNRNPC / CLTC uploads).**
- Neutrophil elastase / STING (THP-1) adds a second STING product, MA5-26032 (stamped 2020-03-04).
- Same experiment, likely legitimate: Bax / vimentin double stain (MA5-51189, MA5-35320); ApoC3 /
  cytokeratin 2e double-stained IHC (MA5-42767, MA5-42788, same timestamp); VPS35 / Vps26a (retromer
  partners, MA5-42386 / MA5-34647 / MA5-34664, same timestamp).
- Same target (likely legitimate): PDGFRB, PTP1B, KRAS, AP-1, MUC1, CK1 alpha, STING, COX2, RHEB,
  CALCOCO2, PSMB9, PECAM-1, KPNA2, SATB1, cytokeratin 5, KLF2 product pairs.
- Dark pairs: 7 new; 4 tagged hubs; the other 3 false by eye.
- Blots (1,335 new): template scan 40 hit products, 38 already in Richardson's lists. The two unlisted
  hits are false: MA5-24236 (pattern C) has no lane-grain match to FLT3 MA5-38523 (peak 0.033, at the
  noise level), and MA5-15313 has a different band and background from MA5-17126. Pattern A: 0 hits.

Eleventh batch (10,207 figures; crawl at ~16,500 MA5/PA5 pages):
- **Thrombospondin 2 MA5-46937 and glucocorticoid receptor MA5-46938 carry the same whole figure** (green
  channel plus a red cytoskeleton merge, 10 um scale bar), both stamped 2023-05-08 13:06:52. The captions
  disagree: GR says HeLa cells; TSP2 says "mock and transfected 293T cells", but the figure has no
  mock / transfected comparison and the caption does not mention the red channel. The staining is nuclear
  and cytoplasmic, which fits GR better than a secreted protein. This could be an upload mix-up rather
  than reuse; it is a stained panel, not a control.
- **HEK 293 group grows: ATP1A1 MA5-36259 (stamped 2022-08-18)** shares the no-primary panel with PKC delta
  MA5-32482 (figure 3) and GLUT1 MA5-37843.
- **USP14 MA5-24727 (stamped 2023-02-13) shares the no-primary panel of PTGES2 MA5-26128 (2023-01-12).**
- RRM2 MA5-27318, PPP1CB MA5-32936, FZR1 PA5-100535 and BAF57 PA5-89181: same no-primary panel, all
  stamped 2021-03-23 11:04:06 (same batch, lower concern).
- Muromonab MA5-47769 / CD2 MA5-47805: same isotype-control panel, same timestamp (lower concern).
- Same or related target (likely legitimate): PDI / P4HB (the same protein), PDPK1 / phospho-PDPK1,
  VPS35 / Vps26a, pericentrin, BCL-10, MUC1, CUGBP1, F4/80, TSPO, SOX17, MMP-9, PGP9.5, desmin, CDCP1, Ntrk1.
- Dark pairs: 8 new; 5 tagged hubs; the other 3 false by eye.
- Blots (1,411 new): template scan 26 hit products, 25 already in Richardson's lists. The unlisted hit
  MA5-26905 (pattern C) is false: a single K562 band at ~22 kDa, unlike MA5-17126. Pattern A: 0 hits.

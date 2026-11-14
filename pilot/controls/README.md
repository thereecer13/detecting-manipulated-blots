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
- Blots (1,335 new): template scan 40 hit products, 38 already in Richardson's lists. Of the two unlisted
  hits, MA5-24236 (pattern C) has no lane-grain match to FLT3 MA5-38523 (peak 0.033, at the noise level);
  MA5-15313 is unresolved (see the batch 13 note on pattern C checks). Pattern A: 0 hits.

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
  MA5-26905 (pattern C) is unresolved (see the batch 13 note on pattern C checks). Pattern A: 0 hits.

Twelfth batch (10,784 figures; crawl at ~18,000 MA5/PA5 pages):
- **HSPA2 MA5-35691 and FGF1 MA5-35690 carry the same whole stained figure** (orange stain, and the same
  field merged with DAPI), both stamped 2023-10-10 09:20:56. The captions name different cells: HSPA2 says
  C6 (rat glioma), FGF1 says U-2 OS (human osteosarcoma).
- **Active/pro-caspase 3 MA5-54044 and AKT1 MA5-54172 carry the same whole stained figure** (DAPI,
  magenta, merge), both "C2C12", both stamped 2025-12-09 22:07:27. Two different targets, one image.
- **DNM1L MA5-26249 (SH-SY5Y) and PKM1 MA5-14815 (MDA-MB-231) share a no-primary panel.** The panel's
  sparse, rounded cells look like the PKM1 figure's cells, not the densely packed cells in the DNM1L
  panels a-d.
- New shared no-primary panels, HeLa: GSK3B PA5-104555 (2021-03-23) / GORASP1 MA5-25160 (2021-05-27);
  GBA MA5-35236 (2025-07-15) / ALPL MA5-42414 (2026-04-29, nine months later).
- ISG15 MA5-29371 (A549 + IFN alpha) / NQO1 MA5-15044 (A549): same no-primary panel.
- Groups grow: RAN / RAG2 / Cyclin B2 / Ku80 adds a second Ku80 product (MA5-14953); Prohibitin / SDHA adds
  Profilin 1 MA5-25120 (HeLa).
- Same batch, lower concern: IGF1R / Lyn (2021-03-23), MUC1 / VASP (2022-08-18), PROX1 / ISL1 (2024-05-21).
- Same target (likely legitimate): angiotensinogen, S100A9, PGP9.5, Lyn, ACTA1, TXN, PSMB9, p16INK4a.
- Dark pairs: 10 new; 9 tagged hubs; the other 1 false by eye.
- Blots (1,407 new): template scan 34 hit products, 33 already in Richardson's lists; the unlisted
  MA5-26551 (pattern C) is unresolved (see the batch 13 note on pattern C checks). Pattern A: 0 hits.

Thirteenth batch (11,357 figures; crawl at ~19,600 MA5/PA5 pages):
- **IkB alpha / EWSR1 group (HeLa and MCF7) adds a second IkB alpha product (MA5-29441, stamped 2020-08-24)
  and Stathmin 1 MA5-16400 (HeLa, 2020-07-13).** The group now spans four products uploaded over five months.
- **Progesterone receptor MA5-14841 (T-47D) and caveolin 1 MA5-16329: same no-primary panel.**
- **RCOR1 MA5-24297 and PRMT4 MA5-15796 (HeLa): same panel, labelled "No Primary antibody" on one and
  "No primary control" on the other.**
- **Integrin beta 1 MA5-27900 (A-431) and VISTA MA5-44265 (2023-06-19): same no-primary panel.**
- CDK9 / KHK (A-431 vs U-87 MG) adds a second KHK product (MA5-25136, U-87 MG); GSK3B / GORASP1 adds a second
  GORASP1 product (MA5-25148).
- Same batch, lower concern: TRBP MA5-38184 / TSC2 MA5-35293 / MYD88 MA5-32246 (HeLa, 2023-02-13 08:26:54,
  the same stamp as USP14 MA5-24727); CLEC4A / CD154 isotype panel (2023-09-05, the same stamp as
  muromonab / CD2).
- Same target (likely legitimate): citrate synthase, KHK, EWSR1, GORASP1, aconitase 2, HA tag, PR, OAS2, ASH2L,
  LGR5, IGF2BP3, cytokeratin 5.
- Dark pairs: 11 new; 6 tagged hubs; the other 5 false by eye.
- Blots (1,433 new): template scan 35 hit products, 34 already in Richardson's lists; unlisted MA5-26600
  (pattern C, share 0.475).

Note on the unlisted pattern C hits (MA5-15313, MA5-26905, MA5-26551, MA5-26600). Pattern C is a shared
background grain under different bands, so different bands do not rule a hit out; earlier notes that did so
are withdrawn. Neither check finds a match: match_overlay gives 0-4% against MA5-17126's Thermo image, and
the lane-grain shift test (with a fallback lane finder for the frameless grey strips these blots use) gives
no isolated peak against MA5-17126 or member MA5-31771 (peaks 0.04-0.14, each within the off-peak p99).
But both checks are weak here: match_overlay also gives 0% for two listed pattern C members against
MA5-17126, and only one of three listed member-member pairs gives a clear shift peak (MA5-31771 / MA5-31894:
0.38 at (0, 0)). These four stay unresolved rather than false.

Fourteenth batch (12,272 figures; crawl at ~21,900 MA5/PA5 pages):
- **NADPH-cytochrome P450 reductase MA5-24977 (HeLa, 2021-03-23) and Histone H3.3 phospho-S31 MA5-44190
  (2022-07-06): the same panel is labelled "No Primary antibody" on POR and "H3.3 (phospho S31) HeLa
  (Untreated)" on the histone product.** One of the two labels is wrong: a no-primary control shown as a
  stained result, or the reverse.
- **Rab9a MA5-35602 (caption: HeLa) and RACK1 MA5-34809 (caption: HEK-293): same no-primary panel**, same
  stamp (2022-08-18), captions disagree on the cell line.
- **BCL-10 MA5-14756 and MA5-32327 (HeLa, 2020-11-30) and fumarase MA5-27745 (HeLa, 2021-03-23): same
  no-primary panel**, four months apart.
- **BCL11B MA5-32546 (A549, 2022-11-28) and SENP1 MA5-35519 (A549, 2023-04-18): same no-primary panel**
  at different display levels.
- **GAPDH MA5-33140 (HeLa, 2026-01-06) and HSPE1 MA5-35686 (HeLa, 2024-03-05): same no-primary panel**,
  two years apart. A second GAPDH product (MA5-31976) shares it under HSPE1's stamp.
- **BMP-8B MA5-27733 and ZFP57 MA5-23521 (293T, same stamp 2020-03-19): the same green-channel stained
  panel** on two products for different targets (both captions: mock and transfected 293T).
- RAD54L2 / Survivin adds SCF MA5-26328 (HeLa, no stamp). DNM1L / PKM1 adds two more DNM1L products
  (MA5-26250, MA5-26255). HEK 293 group adds a second ATP1A1 product (MA5-32184). Prohibitin / SDHA adds
  a second prohibitin (MA5-15899). ALPL / GBA adds a second GBA (MA5-38382, 2025 vs ALPL 2026).
- Same batch, lower concern: GP130 / Caveolin 2 (HeLa, 2019-12-09); BAD / A-Raf (HeLa, 2021-03-23);
  COX1 / FANCA (A549, 2023-01-12); MUC1 / p21 isotype panel (MCF7, 2024-06-28); PHD1 / PDK1 (HeLa, no stamp).
- Same target (likely legitimate): IFITM3, AGTR1, nestin, caspase 6, Cas9, beta-tubulin, ATP5F1B, TOLLIP,
  GBA, SDHA, COX2, ABCC1, CD81, PECAM1, DNM1L, ErbB2.
- Dark pairs: 28 new; 18 tagged hubs; the other 10 (7 distinct) false by eye.
- Blots (2,054 new): template scan 59 hit products, 57 already in Richardson's lists. Unlisted MA5-26534
  (NDUFS2, pattern C, share 0.265): shift test peak 0.146 at (-12, 3) vs MA5-17126 (p99 0.135) and 0.145 at
  (12, 0) vs MA5-31771 (p99 0.118), neither at (0, 0); unresolved. Unlisted MA5-15880 (pattern A, share
  0.54) is a published third-party figure (J Cell Mol Med, multi-panel); the match is on white background
  and the dedicated pattern A detector gives 0 hits; false. Pattern A detector: 0 hits.

Fifteenth batch (12,811 figures; crawl at ~23,500 MA5/PA5 pages):
- **TRAIL-R2 MA5-32693 (HCT 116, 2020-07-13) and PRMT1 MA5-27756 (HCT 116, 2019-12-09): same no-primary
  panel**, seven months apart.
- RRM2 / PPP1CB / FZR1 / BAF57 group adds S100A6 MA5-26658 (same 2021-03-23 stamp). Its caption says U-87 MG;
  the group's earlier captions say A-431.
- SUMO1 / BAK group adds a second BAK product (MA5-32111, A-431, 2022-10-10); the group now spans 2022 to 2026.
- MEKK2 / MYST1 / Map3k2 (A549) adds another MYST1 product (MA5-38064, 2024-05-21).
- COX1 / FANCA (A549, 2023-01-12) adds cyclophilin 40 MA5-35640 (same stamp).
- Same batch, lower concern: MTDH MA5-37800 and MA5-15564 / BRAF MA5-32846 (MCF7, 2024-06-20);
  tocilizumab MA5-48062 / CD64 MA5-48056 isotype panel (U937, 2023-09-05).
- Same target (likely legitimate): TP53, PP2A alpha, PTP1B, IGF2BP3, histone H3, AKT1, Strep tag II, VEGF,
  STAT6, p53.
- Dark pairs: 4 new non-hub pairs, all false by eye.
- Blots (1,459 new): template scan 46 hit products, all already in Richardson's lists. Pattern A: 0 hits.

Sixteenth batch (13,422 figures; crawl at ~25,100 MA5/PA5 pages):
- **Progesterone receptor MA5-14841 and estrogen receptor alpha MA5-14501 (both T-47D): the same stained
  "Composite" panel (green nuclear signal, panel d)** appears in PR's main ICC figure and in ER alpha's
  antibody-validation figure. Two different antibodies cannot give the same image.
- **The PR / caveolin 1 no-primary group (batch 13) adds ER alpha MA5-14501 and a second PR product
  (MA5-16394).** Same panel f on PR, caveolin 1 and ER alpha.
- **Fumarate hydratase MA5-27746 (HeLa, 2020-11-30) and NPM1 MA5-12508 (HeLa, no stamp): same no-primary
  panel.**
- RRM2 / PPP1CB / FZR1 / BAF57 / S100A6 group adds RRM1 MA5-26497 (same 2021-03-23 stamp; caption A-431).
- S100A6 MA5-32511 (caption SH-SY5Y) and KHK MA5-25174 share a no-primary panel (same 2021-03-23 stamp).
- Same batch, lower concern: NKG2D MA5-51623 / 4-1BB MA5-51586 isotype panel (2024-06-28).
- Same target (likely legitimate): EphB4, PTPN1, NuMA, phospho-H2A, cadherin-17, PKA, phospho-RNA pol II,
  CDK1, H3 trimethyl, influenza NP, RhoGDI, angiotensinogen, GPC3, KHK, CCDC.
- Dark pairs: 11 new; 9 distinct non-hub pairs, all false by eye.
- Blots (1,365 new): template scan 36 hit products, all already in Richardson's lists. **The pattern A
  detector gave its first hit (MA5-33115 vs exemplar PA5-99645, share 0.5), but it is false:** the image is
  a published third-party multi-panel figure (Exp Ther Med, butorphanol in PC12 cells), the matched box
  spans the chemical structure and bar charts rather than a blot lane, and the correlation is 0.054.

Seventeenth batch (14,034 figures; crawl at ~26,650 MA5/PA5 pages):
- **SUMO1 / BAK group (A-431) adds TCF7L2 MA5-32240 (stamped 2021-05-27).** The same no-primary panel now
  appears on four products uploaded 2021-05-27, 2022-06-03, 2022-10-10 and 2026-01-06.
- **RAN / RAG2 / Cyclin B2 / Ku80 group (HeLa) adds JNK2 MA5-32191 (2019-12-09) and a second Ku80 product
  (MA5-16375).** RAG2's copy is stamped 2019-03-19, RAN's 2020-01-14.
- **RAD54L2 / Survivin / SCF (HeLa) adds Plastin-3 MA5-27772 (2021-11-15).** Survivin's copy is stamped
  2020-07-13 and RAD54L2's 2022-03-01.
- **TRBP / TSC2 / MYD88 group (HeLa, 2023-02-13) adds a second MYD88 product (MA5-35251) stamped 2023-03-09.**
- Rab9a / RACK1 (captions HeLa vs HEK-293, 2022-08-18) adds a second Rab9a (MA5-31997) and a second RACK1
  (MA5-35405), same stamp.
- RRM2 / PPP1CB / FZR1 / BAF57 / S100A6 / RRM1 (2021-03-23) adds CD2AP MA5-33009 (same stamp).
- The ten-product HeLa group gains new cross-links only (SMARCC1, SP1, PRMT5, LDHB, HNRNPC, CLTC, XPO1 to
  ADAR1's copy); no new products.
- Same target (likely legitimate): K-Ras, CD44, CD147, PGP9.5, Arntl, DTYMK.
- Dark pairs: 3 new non-hub pairs (2 distinct), false by eye.
- Blots (1,435 new): template scan 37 hit products, all already in Richardson's lists. Pattern A: 0 hits.

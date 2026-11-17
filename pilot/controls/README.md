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

Eighteenth batch (14,642 figures; crawl at ~28,250 MA5/PA5 pages):
- **The POR / Histone H3.3 phospho-S31 panel (batch 14) is also on two more POR products, MA5-24967 and
  MA5-24964 (HeLa, 2021-03-23).** It is labelled "No Primary antibody" on all three POR products and
  "H3.3 (phospho S31) HeLa (Untreated)" on MA5-44190.
- **RAD54L2 / Survivin / SCF / Plastin-3 (HeLa) adds hepatocyte growth factor receptor MA5-14847
  (2020-08-24).** The group now has five products uploaded between 2020-07 and 2022-03.
- **SUMO1 / BAK / TCF7L2 (A-431) adds a second TCF7L2 (MA5-14935, 2021-05-27) and a third BAK (MA5-36225,
  2022-10-10).** Six products, 2021 to 2026.
- **ZFP36 MA5-24972 and MA5-25406 (2019-12-09) and COX2 MA5-14568 (2019-11-05), RAW 264.7 + LPS: same
  no-primary panel**, five weeks apart; it appears in both the main and the validation figures.
- **Aurora B MA5-15321 (HeLa and T-47D, 2019-11-05) and MKK7 MA5-32362 (HeLa, 2019-12-09): same no-primary
  panel.**
- NME1 MA5-30707 (HeLa, no stamp) and AQP1 MA5-32593 (HeLa, 2019-11-04): same no-primary panel.
- HSP90 alpha MA5-25036 (HeLa, no stamp) and HSP27 MA5-33170 (validation figure): same no-primary panel.
- BCL11B / SENP1 adds a second SENP1 product (MA5-34767, 2023-03-16). Prohibitin / SDHA / Profilin 1 adds a
  third prohibitin (MA5-32000) and a second profilin (MA5-25113). ACLY / ALDH1A1 / Bcl-xL: new cross-links
  only.
- Same target (likely legitimate): caspase 6, SLC7A11, LAMP1, 53BP1, STAT, RHEB, phospho-RNA pol II.
- Dark pairs: 2 new non-hub pairs, both false by eye.
- Blots (1,352 new): template scan 37 hit products, 34 already in Richardson's lists. Unlisted pattern C hits
  MA5-26536 (share 0.35 vs MA5-17126), MA5-37951 (0.21 vs MA5-38523) and MA5-55374 (0.22 vs MA5-38523).
  Shift test: no isolated peak for MA5-26536 or MA5-37951 against MA5-17126, MA5-31771 or MA5-38523 (all
  peaks within 0.005 of p99, none at (0, 0)); the lane finder fails on MA5-55374. All three unresolved.
  Pattern A: 0 hits.

Nineteenth batch (15,235 figures; crawl at ~29,780 MA5/PA5 pages):
- **SUMO1 / BAK / TCF7L2 (A-431) adds ADAR PA5-78729 and two Toll-interacting protein products
  (MA5-26308, MA5-28676), all stamped 2021-05-27 with captions saying U-87 MG.** The same no-primary panel
  is described as A-431 on the SUMO1/BAK/TCF7L2 products and as U-87 MG on ADAR and TOLLIP. Nine products.
- **The RAN / RAG2 / Cyclin B2 / Ku80 / JNK2 group (HeLa) adds CHEK1 MA5-32180 (2019-12-09) and AGFG1
  PA5-30234 (no stamp).** AGFG1 and Cyclin B2 carry the panel relabelled "No Primary Control" in a different
  font. Eight products, 2018 to 2020.
- **IkB alpha / EWSR1 / Stathmin 1 adds GTF2B MA5-24864 (HeLa, 2020-03-04)**, the same upload stamp as
  EWSR1, whose caption says MCF7. Five products.
- **The PR / caveolin 1 / ER alpha no-primary group adds the PR polyclonal PA5-68778.** Note the caveolin 1
  caption says A-431 while the PR and ER alpha captions say T-47D, for the same panel.
- SMARCB1 / ERG (HeLa) adds E2F2 PA5-77950 (HeLa, 2020-03-04, same stamp as SMARCB1).
- MTDH / BRAF (MCF7, 2024-06-20) adds a third MTDH product (MA5-36100).
- CD38 MA5-47876 / CD37 MA5-47852 (Daudi, 2023-09-05): same isotype control panel (same batch, lower
  concern, like the other isotype pairs).
- Same target (likely legitimate): LAMC1, FAS, MTDH, PR (SK-BR-3 negative panel), RNA pol II pS5 / POLR2A.
- Dark pairs: 4 new non-hub pairs, all false by eye.
- Blots (1,473 new): template scan 19 hit products, all already in Richardson's lists. Pattern A detector:
  13 hits, 12 already listed (share 0.79 to 1.0); the two unlisted (MA5-15738-BTIN 0.33, MA5-32100 0.15) are
  published journal figures (Sci Rep, Wiley) on white backgrounds, false.

Twentieth batch (16,072 figures; crawl at ~31,900 MA5/PA5 pages):
- **The RAN / RAG2 / Cyclin B2 / Ku80 / JNK2 / CHEK1 / AGFG1 group (HeLa) adds PRMT1 PA5-17299 (2019-03-19,
  same stamp as RAG2) and HSPA9 PA5-78009.** Ten products, 2018 to 2020.
- **The SUMO1 / BAK / TCF7L2 / ADAR / TOLLIP group adds nucleoside diphosphate kinase B PA5-96679
  (2021-05-27), caption MCF7.** The one panel is now described as A-431, U-87 MG and MCF7. Ten products.
- **RAD54L2 / Survivin / SCF / Plastin-3 / HGFR (HeLa) adds GBA PA5-67940 (2020-08-24).** Six products.
- **PR / caveolin 1 / ER alpha adds a second caveolin 1 product (PA5-32297), caption A-431**, like MA5-16329;
  the PR and ER alpha captions say T-47D.
- NME1 / AQP1 (HeLa) adds GABARAP PA5-78366. PHD1 / PDK1 (HeLa) adds BNIP3L PA5-19958.
- **New pairs:**
  - CHK2 MA5-32220 / ADAM9 PA5-17080 (A-431, both 2021-03-23).
  - Citrate synthase MA5-17265 (2020-10-20) and MA5-17264 (2021-03-23) / MAOB PA5-29824 (2020-10-20),
    Hep G2.
  - Angiotensinogen MA5-29010 and MA5-32372 / UQCRC2 PA5-30204 (Hep G2, 2019-01-22).
  - **Annexin A2 MA5-32689 (caption Hep G2) / ADAM17 PA5-17079 (caption HeLa, 2020-08-24): same panel,
    captions disagree.**
  - HMMR PA5-88546 (HeLa, 2022-03-15) / cereblon PA5-38037 (HeLa, 2022-03-10).
- Same target (likely legitimate): Neuroligin 1, MGMT. MA5-12104 / AK2 PA5-14196 (0.954): different images by
  eye, false.
- Dark pairs: 3 new non-hub pairs, all false by eye.
- Blots (2,139 new): template scan 18 hit products, 17 already in Richardson's lists. Unlisted pattern C hit
  PA5-15332 (share 0.20 vs MA5-15896): shift test peaks 0.043 at (12, 0) vs MA5-17126 and 0.044 at (-1, 12)
  vs MA5-31771, p99 0.034, none at (0, 0): unresolved.
- **Pattern A detector: 23 hits, 22 already listed. The unlisted hit is CaV1.3 PA5-118794 (K562, stamped
  2021-09-23): share 1.0, corr 0.711 against exemplar PA5-99645, in the range of the listed members
  (0.67 to 0.73), with identical lane borders (x 194 to 300).** This is a Thermo product image, not a
  published figure. An independent high-pass background test (sigma 3) did not separate members from
  same-layout non-members (non-members reach 0.64), so it neither confirms nor rules out the hit. Candidate,
  unresolved.

Twenty-first batch (16,651 figures; crawl at ~32,810 MA5/PA5 pages; the container was reclaimed for about
two hours before this check-in, and the shared-panel step needed a longer timeout):
- **The SUMO1 / BAK / TCF7L2 / ADAR / TOLLIP / NDKB group adds LAMTOR1 PA5-78516 (U-87 MG, 2021-05-27) and
  NDUFAF2 PA5-89734 (caption Hep G2, 2021-05-10).** Twelve products; the one panel is now described as
  A-431, U-87 MG, MCF7 and Hep G2.
- **STAT1 MA5-32271 (2020-11-30) and MA5-37072 (2023-06-26) / RAB12 PA5-98523 (2023-06-19), HeLa: same
  no-primary panel**, the STAT1 copies two and a half years apart.
- Fumarase MA5-33010 / S100A6 PA5-31862 (PC-3, both 2021-03-23): same no-primary panel.
- RRM2 / PPP1CB / FZR1 / BAF57 / S100A6 / RRM1 / CD2AP (2021-03-23) adds a second RRM1 product (PA5-17023).
- IkB alpha / EWSR1 / Stathmin 1 / GTF2B adds a second Stathmin 1 product (PA5-17762, HeLa, 2020-07-13).
- SMARCB1 / ERG / E2F2 (HeLa) adds ORC2 PA5-70227 (2020-03-04, same stamp as SMARCB1 and E2F2).
- KLF10 MA5-20125 / PA5-20838 and AK2 PA5-14196 / PA5-20838: non-cell images (heat map, gels), false.
- Dark pairs: 2 new non-hub pairs, both false by eye.
- Blots (845 new): template scan 13 hit products, 12 already in Richardson's lists. Unlisted: GLB1 PA5-49989
  (pattern B, share 0.17 vs PA5-99439, just above the 0.15 cut; stamped 2025-10-08): unresolved. Pattern A
  detector: 23 hits, 22 listed; the unlisted PA5-95265 is a published figure (Animals, corr 0.12), false.

Twenty-second batch (16,929 figures; crawl at ~34,180 MA5/PA5 pages):
- **PLCB2 PA5-102006 (caption THP-1, 2022-10-10) / KDM6A PA5-31828 (caption K-562, 2022-08-18): same
  no-primary panel, captions disagree.**
- RAD54L2 / Survivin / SCF / Plastin-3 / HGFR / GBA (HeLa) adds a second RAD54L2 product (PA5-89311,
  2022-03-01). Seven products.
- S100A6 / KHK (SH-SY5Y, 2021-03-23) adds a third KHK product (PA5-29004, same stamp).
- Same target (likely legitimate): ASC (MA5-32312 / PA5-50915).
- Dark pairs: 3 new non-hub pairs, all false by eye.
- Blots (1,451 new): template scan 15 hit products, 14 already in Richardson's lists. Unlisted pattern C hit
  PA5-85905 (share 0.20 vs MA5-17126): shift test peaks 0.066 at (-1, -12) vs MA5-17126 (p99 0.060) and
  0.042 at (11, 9) vs MA5-31771 (p99 0.039), none at (0, 0): unresolved. Pattern A detector: 25 hits, all
  already listed.

Correction (SUMO1 family, batches 13 to 21). SUMO1 MA5-14877 carries three different ICC figures, each
with its own no-primary panel, and the batch notes chained them into one "SUMO1 / BAK / TCF7L2 / ADAR /
TOLLIP / NDKB / LAMTOR1 / NDUFAF2" group described as one panel captioned in four cell lines. That is
wrong. A panel-level check (pairs linked only when they share the same panel, not the same product) gives
three groups:
- SUMO1 figure ICC1 (2022-06-03) / BAK x4 / TCF7L2 x2: one panel, all captions A-431, 2021 to 2026.
- SUMO1 figure ICC3 (2022-06-03) / ADAR / TOLLIP x2 / LAMTOR1: one panel, all captions U-87 MG.
- SUMO1 figure of 2021-05-27 / NDKB PA5-96679 (caption MCF7) / NDUFAF2 PA5-89734 (caption Hep G2): one
  panel, captions disagree.
The same check on every other group finds no claim that changes: the other multi-panel groups are separate
panels shared by the same products (PR / ER alpha main and validation figures, ZFP36 / COX2, citrate
synthase), the HEK 293 group's three panels were already listed separately, and the RRM2 / PPP1CB group has
a second shared panel (S100A6 MA5-26658 with RRM2, PPP1CB and RRM1). confirmed_pairs.json group names for the
SUMO1 family are updated accordingly.

Twenty-third batch (17,530 figures; crawl at ~35,700 MA5/PA5 pages; groups now checked at panel level):
- RSK1/2/3 MA5-15040 / PLCG1 PA5-85807 (U-87 MG, both 2022-06-03): same no-primary panel.
- FAS MA5-32489 (validation figure, T-47D vs MDA-MB-231, 2021-05-27) / TRPV6 PA5-51295 (T-47D and MCF7,
  2021-03-23): same no-primary panel, two months apart.
- EDF1 PA5-142102 / PRDM14 PA5-142696 (HeLa, both 2023-01-04): same "-ve control" panel.
- SMARCB1 / ERG / E2F2 / ORC2 (HeLa) adds a second ORC2 product (PA5-67313, 2020-03-04); same panel files
  as the existing group.
- Dark pairs: 2 new non-hub pairs, both false by eye.
- Blots (1,550 new): template scan 13 hit products, 12 already in Richardson's lists. Unlisted pattern C hit
  PA5-13181 (share 0.15 vs MA5-31680): shift peaks 0.064 at (-6, -6) vs MA5-17126 (p99 0.058) and 0.077 at
  (12, -9) vs MA5-31771 (p99 0.073), none at (0, 0): unresolved. Pattern A detector: 20 hits, 19 listed;
  the unlisted PA5-14896 is a published figure (ACS Omega, multi-panel, corr 0.18), false.

Twenty-fourth batch (18,056 figures; crawl at ~37,150 MA5/PA5 pages):
- TIF1 gamma PA5-78496 carries two figures from the 2021-03-23 11:04:06 batch, each sharing a different
  existing panel: ICC1 (caption A-431) has the RRM2 / PPP1CB / FZR1 / BAF57 / RRM1 / CD2AP no-primary panel;
  ICC2 (caption SH-SY5Y) has the S100A6 MA5-32511 / KHK (MA5-25174, PA5-29004) panel. Captions agree within
  each panel.
- Same-target pairs (likely legitimate): Histone macroH2A, ALDOC, galectin 1.
- Dark pairs: 1 new non-hub pair (phospho-H2A.X MA5-27753 / HNF1A PA5-142250), false by eye. One review pair
  (PA5-20838 / PA5-27195) is two published figures (gel vs tissue), false.
- Blots (1,504 new): template scan 13 hit products, 11 listed. Unlisted pattern C hits PA5-49843 (share 0.24
  vs PA5-99439) and PA5-62996 (share 0.20 vs MA5-31717): shift peaks 0.048 at (-11, 12) / 0.024 at (-12, -3)
  and 0.046 at (6, -7) / 0.043 at (1, -12) vs MA5-17126 / MA5-31771, none at (0, 0): unresolved. Pattern A
  detector: 11 hits, all already in Richardson's lists.

Twenty-fifth batch (18,622 figures; crawl at ~38,600 MA5/PA5 pages):
- **DNA ligase III PA5-21480 and BRIP1 PA5-27096 (both 2022-06-14): the whole figure is the same image**,
  both stained panels included. The captions disagree: LIG3 "at nucleus", HeLa, 4% PFA at RT for 15 min;
  BRIP1 "at cytoplasm", 293T, 2% PFA in culture medium at 37 C for 30 min. The image shows nuclear staining.
- **Syntenin-1 MA5-32932 / PA5-92419 (caption MDA-MB-231 and MCF7, 2020-11-30) and ERCC1 PA5-77971 (caption
  U-87 MG, 2020-03-04): same no-primary panel**, captions disagree, nine months apart.
- BMAL1 MA5-32750 / MA5-35561 (2022-10-10) and PKA C-alpha PA5-28160 (2023-05-25): same no-primary panel,
  both captions NIH:OVCAR-3, seven months apart.
- PPP2R1A MA5-14952 (HeLa, 2020-07-13) and PRDX1 PA5-27487 (HeLa treated with H2O2, 2020-08-24): same
  no-primary panel, six weeks apart.
- BCL11B / SENP1 (A549) adds PTP1B PA5-109252 (A549, 2023-03-16, same stamp as SENP1 MA5-34767).
- SMARCB1 / ERG / E2F2 / ORC2 (HeLa) adds a second E2F2 product (PA5-41473, 2020-03-04).
- Same target (likely legitimate): eIF4A1, E2F2, MRPS30, NAT10, GRP78.
- Dark pairs: 5 new non-hub pairs, all false by eye.
- Blots (1,453 new): template scan 13 hit products, all listed. Pattern A detector: 29 hits, 28 listed; the
  unlisted PA5-35924 is a published figure (share 1.0 but corr 0.19), false.

Twenty-sixth batch (19,130 figures; crawl at ~40,000 MA5/PA5 pages):
- Prohibitin / SDHA / Profilin 1 adds RPA70 PA5-17377 (caption HeLa, 2020-07-13, same stamp as SDHA
  MA5-27782 / MA5-32598); the RPA70 copy is labelled "e", the Prohibitin copies "f".
- S100A6 / KHK / TIF1 gamma ICC2 (SH-SY5Y, 2021-03-23) adds PPP1CB PA5-28225 (caption SH-SY5Y, same stamp).
  This is a second PPP1CB product; PPP1CB MA5-32936 is in the other 2021-03-23 panel (RRM2 / FZR1, A-431).
- Angiotensinogen / UQCRC2 (Hep G2) adds a third angiotensinogen product (PA5-21520, Hep G2).
- Same target (likely legitimate): angiotensinogen, CBX5, tyrosine hydroxylase / phospho-TH.
- Dark pairs: 4 new non-hub pairs, all false by eye.
- Blots (1,459 new): template scan 16 hit products, 13 listed. Unlisted pattern C hits PA5-85869 (0.20 vs
  MA5-17126), PA5-24986 (0.15 vs MA5-15896) and PA5-25754 (0.17 vs MA5-38523): no shift peak at (0, 0)
  against MA5-17126 or MA5-31771 (peaks 0.029 to 0.055, each just above its p99, at offsets of 4 to 12 px):
  unresolved. Pattern A detector: 22 hits, 21 listed. The unlisted EVL PA5-118886 (WB-1, 2021-09-23; share
  1.0, corr 0.76 to exemplar PA5-99645) is a Thermo image in the same single-lane template (identical marker
  ladder layout and lane frame, band at ~48 kDa): a pattern A candidate like CaV1.3 PA5-118794, unresolved.

Twenty-seventh batch (19,703 figures; crawl at ~41,400 MA5/PA5 pages):
- **Calnexin MA5-35588 (caption HeLa, 2022-10-10) and HADHA PA5-53317 (caption Hep G2, 2021-05-27): the
  same stained panel "a"**, labelled "Calnexin" on one and "HADHA" on the other. In the HADHA figure, panel a
  matches its own composite (d). In the calnexin figure, the DAPI, F-actin and composite panels (b to d) show
  different, elongated cells that do not match panel a. The 2022 calnexin figure carries the 2021 HADHA
  stained channel. Calnexin is an ER membrane protein and HADHA a mitochondrial enzyme.
- eIF4E PA5-86554 carries two figures (2022-06-03), each sharing a different existing panel: ICC1 (caption
  A-431) has the CHK2 MA5-32220 / ADAM9 PA5-17080 panel (2021-03-23); ICC2 (caption U-87 MG) has the
  RSK MA5-15040 / PLCG1 PA5-85807 panel.
- RAN / RAG2 / Cyclin B2 / Ku80 / PRMT1 / HSPA9 / JNK2 / CHEK1 / AGFG1 group (HeLa) adds Radixin PA5-21660
  and RACK1 PA5-17484 (captions HeLa). The RACK1 copy is captioned "No primary control". This RACK1 product
  is not the one in the Rab9a / RACK1 panel.
- POT1 PA5-66996 (2020-08-24) / MCM4 PA5-65088 (2020-11-30): same no-primary panel, both captions SH-SY5Y,
  three months apart; the POT1 copy is labelled "f", the MCM4 copy "e".
- HMMR / cereblon (HeLa) adds a second cereblon product (PA5-78492, 2022-03-01).
- Same target (likely legitimate): cereblon, MRTFA, and DAB2IP PA5-144652 (2024-01-18) / PA5-141039
  (2023-01-04), whose whole figures are identical.
- Dark pairs: 3 new non-hub pairs, all false by eye.
- Blots (1,407 new): template scan 12 hit products, 11 listed. Unlisted pattern C hit PA5-59228 (0.26 vs
  MA5-38647): peaks 0.042 at (-12, 3) and 0.044 at (11, 4), none at (0, 0): unresolved. Pattern A detector:
  23 hits, all listed.

Twenty-eighth batch (20,253 figures; crawl at ~42,800 MA5/PA5 pages):
- **ADAM17 PA5-17079 (caption HeLa, 2020-08-24) and 4EBP1 PA5-17745 (caption HeLa, 2020-07-13): same
  no-primary panel**, six weeks apart. This extends the Annexin A2 MA5-32689 (caption Hep G2) / ADAM17 panel,
  so it is one panel across three products with captions Hep G2 and HeLa.
- RAD54L2 / Survivin / SCF / Plastin-3 / GBA / HGFR (HeLa) adds a second Survivin product (PA5-27087, caption
  HeLa, 2020-11-30).
- RAN / RAG2 / Cyclin B2 / Ku80 / ... / Radixin / RACK1 (HeLa) adds Serpin H1 PA5-83072 (caption HeLa,
  2021-05-27).
- IkB alpha / EWSR1 / Stathmin 1 / GTF2B adds a second EWSR1 product (PA5-19079, 2020-03-04), whose caption
  also says MCF7 while the other members say HeLa.
- Same target (likely legitimate): HAS3, UBE2G2, RAD18, Survivin, EWSR1; MA5-15738 / PA5-32178 carry the same
  published figure.
- Dark pairs: 8 new non-hub pairs, all false by eye.
- Blots (1,455 new): template scan 13 hit products, 11 listed. Unlisted hits: PA5-83441 (0.47 vs PA5-101507,
  a multi-lane blot with a lane-1 ladder): shift peaks 0.020 at (-8, 12) and 0.052 at (-5, -12), none at
  (0, 0): unresolved. PA5-79097 (0.27 vs MA5-17126) is a single lane on white with no frame, so the shift
  test cannot extract a lane: unresolved. Pattern A detector: 25 hits, 24 listed. The unlisted USP24
  PA5-118918 (WB-1, 2021-09-23, the same upload stamp as EVL PA5-118886; share 1.0, corr 0.82 to PA5-104063)
  is in the same single-lane template: a pattern A candidate, unresolved.

Twenty-ninth batch (20,780 figures; crawl at ~44,200 MA5/PA5 pages):
- PTP1B MA5-25574 / MA5-25616 / MA5-25641 / MA5-25642 (captions MCF-7, no stamp) and SCRIB PA5-66680
  (caption MCF7 and Caco-2, 2020-11-30): same no-primary panel, PTP1B copies labelled "e", SCRIB "f".
- Ferritin MA5-14736 (caption Hep G2 and MCF7, 2020-08-24) and MCT1 PA5-76687 (caption Hep G2, 2020-03-04):
  same no-primary panel, five months apart; labelled "f" and "e".
- TWIST1 MA5-17195 / V-ATPase E1 PA5-29899 (HeLa, both 2019-03-19): same no-primary panel.
- DNA-PK MA5-32192 (HeLa, 2019-12-09) / PCM1 PA5-76769 (HeLa, 2020-03-04): same no-primary panel.
- S100A6 / KHK / TIF1 gamma ICC2 / PPP1CB PA5-28225 (SH-SY5Y, 2021-03-23) adds PTPRN PA5-76932 (caption
  SH-SY5Y, same stamp).
- RAD54L2 / Survivin group (HeLa) adds SMARCA5 PA5-52601 (caption HeLa, 2020-07-13, same stamp as Survivin
  MA5-15077). Prohibitin / SDHA / Profilin 1 / RPA70 adds a fourth Prohibitin product (PA5-19556).
- Same target (likely legitimate): PD-L1 MA5-32450 / PA5-88105, FAM3B, adenylate cyclase 3, Prohibitin;
  vimentin MA5-13203 / PA5-27231 carry the same published figure.
- Dark pairs: 4 new non-hub pairs, all false by eye.
- Blots (1,517 new): template scan 8 hit products, 7 listed. The unlisted PA5-19216 (0.21 vs MA5-38647) is a
  three-strip blot (A, B, C) without a lane frame; the shift test cannot extract a lane: unresolved.
  Pattern A detector: 21 hits, 19 listed. ELF5 PA5-118893 (WB-1, 2021-09-23, the EVL / USP24 upload stamp;
  share 1.0, corr 0.69) is in the same single-lane template: a third pattern A candidate from that upload,
  unresolved. PA5-109274 is a published figure (bar charts and strips, corr 0.09), false.

Thirtieth batch (21,341 figures; crawl at ~45,670 MA5/PA5 pages):
- **ASC MA5-32312 (caption MCF7, 2020-10-20) / PA5-50915 (2020-11-30) and MDA5 PA5-89344 (caption A549 treated
  with IFN gamma, 2021-07-01): same no-primary panel**, captions disagree. The ASC pair was earlier listed as
  same target; with MDA5 it is a cross-target panel.
- TORC2 PA5-142679 / TERT PA5-142844 (both HeLa, 2023-01-04): same "-ve control" panel.
- CD63 MA5-30187 (Jurkat, 2020-12-26) / MCT2 PA5-76603 (Jurkat, 2020-10-20): same no-primary panel.
- Syntenin-1 / ERCC1 (captions MDA-MB-231 and MCF7 vs U-87 MG) adds a second ERCC1 product (PA5-29158, caption
  U-87 MG, 2020-03-04).
- RAN / RAG2 / Cyclin B2 / Ku80 / ... / Serpin H1 group (HeLa) adds TRIM25 PA5-27229 (caption HeLa,
  2021-05-27, the Serpin H1 stamp). RAD54L2 / Survivin / SMARCA5 group (HeLa) adds a third RAD54L2 product
  (PA5-50258).
- Same target (likely legitimate): Tgoln2, EphB4, EPS8, ERCC1, RAD54L2; Oncostatin M PA5-120974 / PA5-76861 and
  VAPB PA5-76727 / PA5-110563 share figures across the 2023-10-10 and 2024-10-25 uploads.
- Dark pairs: 5 new non-hub pairs, all false by eye.
- Blots (1,462 new): template scan 13 hit products, 11 listed. Unlisted PA5-19534 (0.20 vs MA5-17126): shift
  peaks 0.111 at (-10, 2) and 0.122 at (-12, 0), none at (0, 0): unresolved. Unlisted PA5-14903 (0.18 vs
  MA5-15887): peaks 0.038 at (-12, 8) and 0.039 at (12, 6), none at (0, 0): unresolved. Pattern A detector: 31
  hits, 30 listed; the unlisted PA5-27338 is a published figure (corr 0.15), false.

Thirty-first batch (21,905 figures; crawl at ~47,070 MA5/PA5 pages):
- **Fra1 PA5-76185 (2019-12-09) and CDC25B PA5-17759 (2020-03-04): a "negative cell line" panel in one figure
  is the no-primary panel in the other.** Fra1's panel e is labelled "CLDN5 HeLa(Negative)", naming a different
  target; the same image is CDC25B's panel f, labelled "No Primary antibody". CLDN5 MA5-32614's own
  "HeLa (Negative)" panel shows different cells, so the CLDN5 label is a leftover from a template. Fra1's
  own no-primary panel f is a different image. Captions: U-87 MG and HeLa (Fra1) vs HeLa and serum-starved
  HeLa (CDC25B).
- RAN / RAG2 / Cyclin B2 / Ku80 / ... / Serpin H1 / TRIM25 group (HeLa) adds CBX5 PA5-82556 (caption HeLa,
  2021-05-27, the Serpin H1 / TRIM25 stamp).
- SUMO1 / NDKB (MCF7) / NDUFAF2 (Hep G2) adds a second NDUFAF2 product (PA5-63019, caption Hep G2, 2021-05-11).
- Same target (likely legitimate): NDUFAF2, FABP7, PLCG1, Tsg101, H3K36me3; PA5-41758 / PA5-43290 share a
  HeLa IF figure; PA5-28647 / PA5-12447 are published figures.
- Dark pairs: 6 new non-hub pairs, all false by eye.
- Blots (1,453 new): template scan 11 hit products, all listed. Pattern A detector: 24 hits, all listed.

Thirty-second batch (22,420 figures; crawl at ~48,470 MA5/PA5 pages):
- **GLI3 MA5-42801 (caption NIH/3T3, a mouse line) and AGPS PA5-87935 (caption U2OS, a human line): the same
  stained figure**, both the target channel and the DAPI merge, uploaded the same day (2023-10-10). The
  captions name different targets, cell lines and species.
- COX1 / FANCA / cyclophilin 40 MA5-35640 (A549, 2023-01-12) adds a second cyclophilin 40 product (PA5-27988,
  caption A549, 2023-02-13).
- NME1 / AQP1 / GABARAP (HeLa) adds a second NME1 product (PA5-79742, no stamp).
- Prohibitin / SDHA / Profilin 1 / RPA70 (HeLa) adds Cofilin PA5-19727 (caption HeLa, no stamp).
- RAN / RAG2 / ... / CBX5 group: another RAG2-CBX5 link, nothing new.
- Same target (likely legitimate): NME1, HSPB8, RhoGDI, IRF5, GBA3, PABPC4, POLR2J, YY1, GMNN; PA5-41758 /
  PA5-43290 / PA5-41802 share a HeLa IF figure.
- Dark pairs: no new non-hub pairs.
- Blots (1,469 new): template scan 12 hit products, 10 listed. Unlisted PA5-40591 (pattern A, 0.16) is a
  published figure, false. Unlisted PA5-51546 (pattern B, 0.19 vs PA5-99439) is a two-lane SK-MEL-30 / HEK 293
  blot in the standard layout with an RNA panel; at this share it is not checked further: unresolved.
  Pattern A detector: 19 hits, all listed.

Thirty-third batch (22,988 figures; crawl at ~49,920 MA5/PA5 pages):
- TRBP / TSC2 / MYD88 (HeLa, 2023-02-13 and 2023-03-09) adds a second TSC2 product (PA5-95194, caption HeLa,
  2023-02-13).
- SUMO1 / NDKB (MCF7) / NDUFAF2 (Hep G2) adds TIMM10 PA5-76173 (caption Hep G2, 2021-05-27, the SUMO1 / NDKB
  stamp).
- Same target (likely legitimate): ENOX2, CRX, NeuN, Profilin 1, TSC2.
- Dark pairs: 1 new non-hub pair and 1 review pair, both false by eye.
- Blots (1,464 new): template scan 14 hit products, 12 listed. Unlisted PA5-11652 (pattern C, 0.19 vs
  MA5-15887): shift peaks 0.056 at (5, -4) and 0.064 at (-4, -12), none at (0, 0): unresolved. Unlisted
  PA5-49926 (pattern B, 0.30 vs PA5-99439) is a two-strip FGF23 blot in the same strip layout; not checked
  further: unresolved. Pattern A detector: 20 hits, all listed.

Thirty-fourth batch (23,549 figures; crawl at ~51,345 MA5/PA5 pages):
- **Blot: PTPN22 PA5-118870 (WB-1, stamped 2021-09-23) matches Richardson's background pattern B**
  (exemplar GRB14 PA5-101612, 2019-08-08; share 0.89, corr 0.90 at zero offset). With contrast stretched,
  both blots show the same background: a dark streak down lane 1, a dark lower-left corner and the same
  mottling, while the bands sit at different weights (about 90 kDa for GRB14, about 60 kDa for PTPN22).
  PA5-118870 is not in Richardson's lists. It carries the 2021-09-23 upload stamp of the unresolved pattern
  A candidates EVL, USP24 and ELF5.
- Profilin 1 PA5-22991 / PA5-27612 (caption HeLa, no stamp) and ATG13 PA5-75682 (caption HCT 116,
  2020-03-04): same no-primary panel, captions disagree.
- GSTM3 PA5-142352 (HeLa, 2023-01-04) / FXR1 PA5-18556 (HeLa, 2024-02-01): same "Negative Control" panel,
  13 months apart.
- RAD18 PA5-52602 / PA5-52331 and NMP84 PA5-69083 (HeLa, no stamps): same no-primary panel.
- TGN46 PA5-23068 / TRAP1 PA5-30358 (HeLa, no stamps): same no-primary panel.
- Citrate synthase / MAOB PA5-29824 (Hep G2) adds a second MAOB product (PA5-79624, 2020-10-20).
- Fumarase / S100A6 PA5-31862 (PC-3, 2021-03-23) adds Lyn PA5-27361 (caption PC-3, same stamp).
- SMARCB1 / ERG / E2F2 / ORC2 (HeLa) adds a second SMARCB1 product (PA5-53764, 2020-03-04).
- Same target (likely legitimate): MAOB, PSMB10, ATG13, SMARCB1; MA5-12902 / PA5-68465 published figures.
- Dark pairs: 1 new non-hub pair, false by eye.
- Blots (1,413 new): template scan 7 hit products, 6 listed (the unlisted one is PTPN22 above). Pattern A
  detector: 22 hits, all listed.

Thirty-fifth batch (24,090 figures; crawl at ~52,735 MA5/PA5 pages):
- GSTP1 MA5-15309 / MA5-29313 (caption PC-3, 2020-11-30) and MA5-27913 (2021-03-23) with alpha-actinin-4
  PA5-97731 (caption PC-3, 2021-11-11): same no-primary panel, labelled "f" in all four products.
- MAO-B PA5-18442 / CK1 epsilon PA5-18704 (HeLa, both 2024-02-01): same "-ve control" panel.
- ASC / MDA5 (captions MCF7 vs A549 + IFN gamma) adds a second MDA5 product (PA5-82028, caption A549 + IFN
  gamma, 2021-07-01), so the panel is on five products.
- IkB alpha / EWSR1 / Stathmin 1 / GTF2B (captions HeLa and MCF7) adds Coilin PA5-66995 (caption HeLa, no stamp)
  and a second GTF2B product (PA5-28556, 2020-03-04).
- RSK / PLCG1 (2022-06-03) adds RSK1 PA5-90646; this panel's captions say NTERA-2 cl.D1 (MA5-32276 / PA5-90646)
  as well as U-87 MG (MA5-15040 / PA5-85807).
- Same target (likely legitimate): FOXA1, TFAP2, GTF2B, ING5, MDA5, VCP, PRDX5, AIPL1, SBP2, PLCG1.
- Dark / review pairs: 4 new non-hub pairs (published figures), all false by eye.
- Blots (1,444 new): template scan 15 hit products, 12 listed. Unlisted:
  - SOS2 PA5-118863 (WB-1, stamped 2021-09-23; template pattern A 0.57 vs PA5-102052; pattern A detector
    share 0.75, corr 0.38): single lane in the same template. The fourth candidate from the 2021-09-23
    upload (with EVL, USP24, ELF5; PTPN22 from that upload matched pattern B). Unresolved.
  - DOCK7 PA5-68163 (WB-1, 2025-10-08; template 0.23; detector share 0.73, corr 0.38): single lane in the
    same template; with contrast stretched it shows a pale patch at 37-50 kDa like the exemplar PA5-99645.
    Unresolved.
  - PA5-50087 (pattern B, 0.15) is a single-strip PHF3 blot in a different layout: false.
  Pattern A detector: 25 hits, 23 listed (the two above).

Thirty-sixth batch (25,068 figures, 56,087 panels; crawl at ~55,300 MA5/PA5 pages). The first attempt ran out of
memory (16 GB); `shared_panels.py` now keeps its 160-px verification panels as uint8 instead of float32.
- S100A8 MA5-17621 / MyD88 PA5-19919 (caption SK-BR-3, both stamped 2019-11-05): same no-primary panel (f).
- PLZF MA5-15667 (HeLa, 2020-07-13, labelled "e") / PML PA5-51039 (HeLa, 2020-03-04, labelled "f"): same
  no-primary panel under different panel letters.
- PRKAR1B MA5-25517 (no stamp) / CRKL PA5-28622 (2020-11-30), both captioned SH-SY5Y: same no-primary panel.
- CYP2E1 MA5-32605 (no stamp) / 14-3-3 epsilon PA5-28937 (2020-03-04), both Hep G2: same no-primary panel.
- GMNN PA5-30612 and PA5-76710 / Golgin-97 PA5-30048 (HeLa, no stamps): same no-primary panel.
- FXR PA5-18620 / Kallikrein 6 PA5-143104 (U2OS, both 2024-02-01): same "-ve control" panel.
- SUMO1 MA5-14877 ICC2 (U-2 OS, 2022-06-03; the panel shared with BAK MA5-33215) also appears as the
  no-primary panel of ZC3H12A PA5-83215 (U-2 OS, 2021-08-03), ten months earlier.
- SUMO1 / NDKB / NDUFAF2 / TIMM10 adds a second SUMO1 product (PA5-24560, Hep G2, same stamp 2021-05-27 as
  MA5-14877); RAD54L2 / Survivin group (HeLa) adds a third RAD54L2 product (PA5-65253, same stamp 2022-03-01
  as PA5-99087).
- Same target (likely legitimate): PTPN2, TRF2/RAP1, SATB1, SYK, Aqp4, KIR2DL3, BRK, YBX1, RAD54L2, SUMO1.
- False: two published-figure pairs (GPC3 / PA5-27288 microscopy insets) and 3 dark non-hub pairs, by eye.
- Blots (2,626 new): template scan 24 hit products, 22 listed; unlisted EED PA5-92427 (pattern A 0.16) is a
  multi-band HeLa / mouse brain blot and CGKII PA5-49822 (pattern B 0.22) a two-lane HUVEC blot: both false.
  Pattern A detector: 39 hits, 38 listed. Unlisted:
  - SRRM2 PA5-118900 (WB-1, stamped 2021-09-23; detector share 1.0, corr 0.72, the highest correlation seen
    so far vs PA5-99645): with contrast stretched, the lane background shows the exemplar's pale patch at
    37-50 kDa and the same dark mottling, with the band moved from ~180 kDa to ~300 kDa. Strong candidate;
    the sixth blot from the 2021-09-23 upload flagged (EVL, USP24, ELF5, SOS2 pattern A; PTPN22 pattern B).

Thirty-seventh batch (25,878 figures, 57,656 panels; crawl at ~57,400 MA5/PA5 pages). No new cross-target groups;
four existing groups grow:
- TORC2 / TERT "-ve control" (U2OS, both 2023-01-04) adds monoacylglycerol lipase PA5-19001 (caption
  paraformaldehyde-fixed U2OS, stamped 2024-02-01), thirteen months later.
- GSTM3 / FXR1 "Negative Control" adds SHH PA5-142192 (caption HeLa, 2023-01-04, same stamp as GSTM3).
- Annexin A2 / ADAM17 / 4EBP1 adds AIF PA5-17638 (caption HeLa, no stamp).
- PLCB2 / KDM6A adds a second PLCB2 product (PA5-78108, THP-1, same stamp 2022-10-10 as PA5-102006).
- Same target (likely legitimate): NUMB, FABP, Aqp4, TBRG4, Gemin 3, DLG7, SFPQ, ITGB8, MRPS16, PADI2.
- False by eye: AK2 / Ki67 (published figures), 6 dark non-hub pairs, one blot-strip pair.
- Blots (2,123 new): template scan 15 hit products, 13 listed. Unlisted PAR6 PA5-18233 (pattern C 0.22) is a
  two-lane blot in a different layout (false); AKT1 PA5-23780 (pattern C 0.18) shows no zero-offset peak in
  shift2.py against either reference (unresolved, likely false). Pattern A detector: 29 hits, all listed.

Thirty-eighth batch (26,414 figures, 58,603 panels; crawl at ~58,800 MA5/PA5 pages):
- SLK PA5-85695 / SOX4 PA5-41442 (both captioned MCF7, both stamped 2022-07-11): same no-primary panel.
- SMARCB1 / ERG / E2F2 / ORC2 (HeLa) adds EZH2 PA5-17569 (caption HeLa, stamped 2022-03-10); ERG MA5-26261
  carries the same panel stamped 2019-12-09, so the panel spans more than two years of uploads.
- SUMO1 / NDKB / NDUFAF2 / TIMM10 (Hep G2) adds NDUFB9 PA5-21668 (caption Hep G2, 2021-05-11, the same day as
  NDUFAF2 PA5-63019).
- Same target (likely legitimate): PGBD5 (stained panel), DAP, guanine nucleotide-binding protein, KAP3, macroH2A,
  NDUF, POLR2.
- False by eye: 3 dark non-hub pairs.
- Blots (1,398 new): template scan 16 hit products, 15 listed. Unlisted SARS-CoV-2 nucleocapsid PA5-144378
  (pattern C 0.39) is a single-lane recombinant-protein blot in a different layout: false. Pattern A
  detector: 19 hits, all listed.

Thirty-ninth batch (26,973 figures, 59,750 panels; crawl at ~60,250 MA5/PA5 pages). No new cross-target groups;
four existing groups grow:
- RAN / RAG2 / Cyclin B2 / Ku80 / PRMT1 / HSPA9 / CHEK1 / AGFG1 / Radixin (HeLa) adds RAD51 PA5-31144 (caption
  HeLa, no stamp), where the panel is labelled "No primary control" rather than "e".
- RAD54L2 / Survivin / SCF / Plastin-3 / HGFR / GBA / SMARCA5 (HeLa) adds OPA1 PA5-57874 (caption HeLa, no
  stamp).
- S100A6 / KHK / TIF1 gamma / PPP1CB (SH-SY5Y, 2021-03-23) adds SAP102 PA5-78501 (caption SH-SY5Y, same stamp).
- Integrin beta 1 MA5-27900 / VISTA MA5-44265 adds a second ITGB1 product (PA5-78028, caption A-431, no stamp).
- p21 MA5-31479 (2022-06-14) and CDK4 PA5-27827 (2020-03-19) carry the same stained MCF7 figure; both
  captions describe it as a CDK4 (green) / p21 (red) co-stain with both antibodies, so it is legitimate.
- Same target (likely legitimate): MLPH, PTPN2, DNAJC, DOK4, GTF2F, INPP5, SKIP, Integrin beta 1.
- Blots (1,428 new): template scan 11 hit products, 8 listed. Unlisted GPC5 PA5-50185 (pattern B 0.37),
  cytokeratin 7 PA5-85983 (pattern C 0.22; no zero-offset peak in shift2.py) and TMF1 PA5-31184 (pattern C
  0.18) are blots in different layouts: false. Pattern A detector: 16 hits, all listed.

Fortieth batch (27,574 figures, 61,129 panels; crawl at ~61,700 MA5/PA5 pages):
- **B1 bradykinin receptor PA5-18988 (stamped 2021-07-01) and V-ATPase B1 PA5-56878 (stamped 2020-11-30): same
  no-primary panel f, with captions that contradict each other.** BDKRB1's caption: SH-SY5Y cells, goat primary
  with Donkey anti-Goat Alexa Fluor Plus 488 (A32814), nuclei with ProLong Gold. V-ATPase B1's caption: HaCaT
  and BeWo cells, rabbit primary with Donkey anti-Rabbit Alexa Fluor Plus 488 (A32790), nuclei with ProLong
  Diamond with DAPI. A no-primary control tests the secondary antibody, so one panel cannot be the control for
  both. Review image: reviews/thermo_controls/bdkrb1_vatpase.png (outside the repo).
- NME1 MA5-29446 and MA5-29447 / MCM5 PA5-76544 (all captioned HeLa; MCM5 stamped 2020-03-04): same
  no-primary panel.
- GSTM3 / FXR1 / SHH "Negative Control" adds KCNN4 PA5-142531 (caption HeLa, 2023-01-04, same stamp).
- RAN / RAG2 / Cyclin B2 / Ku80 / PRMT1 / HSPA9 / CHEK1 / AGFG1 / Radixin / RAD51 (HeLa) adds a second HSPA9
  product (PA5-79410, caption HeLa, no stamp).
- Same target (likely legitimate): ATGL, CD34, DC-SIGN, HSPA9, KIAA1, NOTCH, WFS1.
- False by eye: 7 dark non-hub pairs and one published-figure review pair.
- Blots (1,474 new): template scan 14 hit products, all listed. Pattern A detector: 15 hits, all listed.

Forty-first batch (28,111 figures, 62,254 panels; crawl at ~63,100 MA5/PA5 pages):
- **CrkL PA5-28622 (stamped 2020-11-30) and SOX11 PA5-40698 (stamped 2019-11-05): one image, two different
  labels.** CrkL labels it "No Primary antibody" (SH-SY5Y). SOX11, the older upload, labels the same image
  "BeWo (Negative)": a cell line with no expression, stained with the SOX11 antibody, not a no-primary
  control. The CrkL / PRKAR1B group (batch 36) now includes SOX11. Review image:
  reviews/thermo_controls/crkl_sox11.png (outside the repo).
- **PPM1A MA5-17154 (stamped 2021-03-23) and TOP1 PA5-78203 (stamped 2019-11-04): same no-primary panel e,
  with captions that contradict each other.** PPM1A's caption: MCF7 cells, mouse monoclonal with Goat
  anti-Mouse Alexa Fluor Plus 488 (A32723). TOP1's caption: HeLa cells, rabbit polyclonal with Goat anti-Rabbit
  Superclonal 488 (A27034). Review image: reviews/thermo_controls/ppm1a_top1.png.
- **AP2M1 MA5-25570 (stamped 2019-11-05) and mtTFA PA5-29571 (stamped 2019-12-09): same no-primary panel e.**
  Both captions say Caco-2, but the secondaries differ: anti-mouse A32723 for AP2M1 and anti-rabbit A32731 for
  mtTFA. Review image: reviews/thermo_controls/ap2m1_mttfa.png.
- NME1 MA5-29446 and MA5-29447 / MCM5 (batch 40) adds RAD21 PA5-28344 (HeLa, stamped 2020-03-04). The secondaries
  differ here too: NME1 uses anti-mouse A28175, RAD21 uses anti-rabbit A32731.
- eIF4E PA5-17919 / GSK-3 beta PA5-78539: same no-primary panel f. Both say HeLa, carry the same 2021-03-23
  stamp and use the same secondary (A32790), so this may be a legitimate shared batch control.
- Tead1 MA5-35679 and MA5-36214 / Bmi1 PA5-110999: same panel e. Both say HeLa and use the same secondary
  (A32790).
- Same image under each pair's "Negative control" / "-ve control" label: ZGLP1 PA5-142561 / OGT PA5-18658 (U2OS);
  HSP60 PA5-143265 / AIF PA5-143222 (HeLa); FARP1 PA5-142075 / GLI1 PA5-142651 (U2OS); EDF1 PA5-142102 /
  GATA1 PA5-18408 (HeLa).
- The SUMO1 ICC2 / BAK panel group adds PH-interacting protein PA5-110105 (A-431, stamped 2021-05-27).
- Same target (likely legitimate): ARHGAP5, ASNA1, CD81, Cytochrome P450 Reductase, DLD, eIF4A1, LDB3,
  Optineurin, PP2A alpha, SQSTM1, TGM2.
- False by eye: 5 dark non-hub pairs and one published-figure review pair (MA5-12104).
- Blots (1,379 new): the template scan hit 12 products. Two were unlisted:
  - **CABP5 PA5-118907 (WB-1, stamped 2021-09-23, again the same upload as SRRM2): pattern A, confirmed by eye.**
    The equalized background matches SRRM2 PA5-118900 and the exemplar PA5-99645: the same pale patch at
    37–50 kDa and the same dark blotches, with a band only at ~20 kDa. Review image:
    reviews/thermo_controls/cabp5_srrm2_patternA.png. The 2021-09-23 upload now has 7 blot candidates.
  - FOXI3 PA5-48217 (pattern C): false; shift-correlation peak 0.05, no higher than the noise.

Forty-second batch (28,479 figures, 62,945 panels; crawl at ~64,000 MA5/PA5 pages):
- Prohibitin / SDHA / Profilin 1 / RPA70 / Cofilin (HeLa, panel e) adds a second Cofilin product, PA5-27627
  (HeLa). Its caption names the rabbit secondary A27034, while Profilin 1 MA5-25120's caption names the
  anti-mouse A28175 for the same panel, so the secondaries conflict.
- The 2022 HeLa no-primary panel group (SMARCC1 / PRMT5 / LDHB / HNRNPC / CLTC / XPO1 / ADAR1) adds SP1
  PA5-95583 and a second ADAR1 product, MA5-34626. All captions say HeLa with A32790, so they are consistent.
- HMMR / cereblon (HeLa, 2022) adds IRF7 PA5-102832, labeled panel f where HMMR's is panel e.
- Same target (likely legitimate): ATP1B2, CDK6, Cofilin, Erg, HAI-2, SDHB, SP1, Tsg101, eIF4E2.
- False by eye: 5 dark non-hub pairs.
- Blots (921 new): template scan 7 hit products, all listed. Pattern A detector: 14 hits, all listed (the
  2019-08-08 upload plus RAB17 PA5-115816). No 2021-09-23 stamps.

## Sorting the 405 confirmed pairs by what their captions say (tier_pairs.py)

For each confirmed pair, the two product captions are compared. Cell lines come from a search of the full
caption against a list of known lines. The species of the secondary antibody comes from the secondary's
catalog number (A32790/A27034/A32731/A32794 anti-rabbit; A32766/A32723/A28175/A32787 anti-mouse; A32814
anti-goat). The upload date comes from the image URL stamp.

| Tier | Rule | Pairs | Groups* |
|---|---|---|---|
| 1a captions contradict: cell line or panel label | no cell line in common, or a conflicting panel label (CrkL/SOX11) | 44 | 19 |
| 1b captions contradict: secondary species only | same cell line, but anti-mouse vs anti-rabbit (or anti-goat) | 90 | 25 |
| 2 probable reuse | captions consistent, upload stamps more than 7 days apart | 89 | 21 |
| 3 plausible batch control | captions consistent, stamps within 7 days | 71 | 20 |
| 4 undetermined | consistent where known, but a stamp or caption detail is missing | 111 | 15 |

*Groups are connected sets of products, ranked by their most severe pair. A group can join products through
different shared panels, so evidence is per pair (pair_tiers.json). Group summary: group_tiers.json.

Caveats: 1b is weaker than 1a. A lab could put both secondaries on a no-primary well, though the captions never
say so. Upload stamps are not experiment dates, so tier 2 vs 3 is only a hint. Tier 1a includes same-day pairs
such as MA5-54064 (HT-1080) / MA5-54052 (C2C12): a no-primary image shows one cell line, so both captions
cannot be right.

Forty-third batch (crawl at ~65,300 MA5/PA5 pages):
- HSP60 PA5-143265 / AIF "-ve control" (HeLa, 2023-01-04) adds a second AIF product, PA5-143221 (same stamp).
- Integrin beta 1 / VISTA (A-431) adds a second VISTA product, PA5-119555 (caption A-431 and HEK293,
  2023-06-19; panel f where ITGB1 has panel e).
- Same target (likely legitimate): Aconitase, DHRS2, GLS, HCLS1, HSP70, KRT9, MIF, MYH11, NLRC4, SERPINA10,
  SRPRB, VSIR.
- False or uninformative by eye:
  - near-blank dark frames shared by the PA5-49xxx family and PA5-34401 (nothing to compare);
  - bead and well images;
  - 4 dark non-hub pairs.
- Blots (1,332 new): template scan 16 hit products, 5 unlisted:
  - **ACVRL1 PA5-118826 (WB-1, stamped 2021-09-23): pattern B, confirmed.**
    - After rescaling to the exemplar size, its lane background matches the 2019-08-08 pattern B exemplars
      TSEN54 PA5-101939 and GRB14 PA5-101612 on raw pixels: texture r = 0.62 and 0.61, falling to 0.02 when
      flipped.
    - It is the first time the 2019 pattern B background appears in the 2021-09-23 upload, which now has
      8 blot candidates.
    - Review image: reviews/thermo_controls/acvrl1_patternB.png.
  - HDAC11 PA5-11249, SC4MOL PA5-48651, ID1 PA5-121198 and GAK PA5-15320 (pattern C): false; shift-correlation
    peaks of 0.03–0.10, at or near the noise level.

Forty-fourth batch (29,328 figures, 64,673 panels; crawl at ~66,100 MA5/PA5 pages):
- **FAF-X MA5-26367 / eIF2B delta PA5-30292 (both A-431, both stamped 2021-03-23): same no-primary panel e,
  but the secondaries conflict.** FAF-X's caption names an anti-mouse secondary and eIF2B delta's an
  anti-rabbit one (tier 1b).
- GTF2IRD1 PA5-142234 / Nrf2 PA5-142785: the same "-ve control" image (both U2OS, both stamped 2023-01-04).
- The HepG2 group (NDUFAF2 / NDUFB9 / SUMO1 / NME2) adds Tim10 PA5-110488 (HepG2, stamped 2021-05-27).
- The U-87 MG group (ADAR1 / LAMTOR1 / TOLLIP / SUMO1) adds ZC3H12A PA5-20926 (U-87 MG, no stamp).
- Same target (likely legitimate): alpha A crystallin, CREM, DNAJA2, DNAJB6, ITGB8, LAT, Tim10.
- False by eye: 3 dark non-hub pairs.
- Blots (861 new): template scan 13 hit products, 2 unlisted:
  - WDR54 PA5-113432 (pattern C, share 0.41): false. It uses a different layout (kDa labels with units), and
    the shift-correlation peak (0.12) is not at (0, 0). Its lane is uniformly flat with no texture.
  - MCART2 PA5-24374 (pattern C, share 0.18): false; peak 0.06, at the noise level.
  - Pattern A detector: 12 hits, all listed. No 2021-09-23 stamps.

Forty-fifth batch (29,663 figures, 65,343 panels; crawl at ~67,100 MA5/PA5 pages):
- CBX5 MA5-32018 and PA5-17441 (HeLa, stamped 2020-08-24) / G3BP1 PA5-90073 (HeLa, stamped 2021-05-27): same
  no-primary panel (e on CBX5, f on G3BP1). The captions are consistent, but the uploads are nine months apart.
- The ILK / FAS / TRPV6 group adds Galectin 1 MA5-32779 (caption MCF7 and MDA-MB-231, no stamp).
- Acetyl-histone H3 (Lys18) MA5-24669 / acetyl-histone H4 (Lys8) PA5-40092 (stamped 2018-01-24): same
  "No Primary" panel f on products for two different histone marks.
- Same target (likely legitimate): ACIN1, GGA2, GOLGA4, POFUT2, RAB13, RSRC1.
- False by eye: published-figure panels (MA5-20125, MA5-12902 vs PA5-106838) and 7 dark non-hub pairs.
- Blots (925 new): template scan 8 hit products, all listed. Pattern A detector: all hits listed.

Forty-sixth batch (30,249 figures, 66,480 panels; crawl at ~68,500 MA5/PA5 pages):
- **The Hep G2 citrate synthase / MAOB group adds GSTM1 PA5-79337, whose caption says HeLa** (tier 1a): the
  same no-primary panel on a product with a different stated cell line.
- The HepG2 group (SUMO1 / NDUFAF2 / NDUFB9 / NME2 / Tim10) adds OASL PA5-81946 (Hep G2, stamped 2021-05-11).
- The HeLa group (IkB alpha / EWSR1 / Stathmin 1 / GTF2B / Coilin) adds NONO PA5-79748.
- The NME1 / AQP1 / GABARAP group adds PDK1 PA5-79797 (HeLa).
- The SOX11 / CrkL / PRKAR1B group adds a second CrkL product, PA5-95058 (SH-SY5Y).
- APAF1 MA5-32082 / FADD PA5-17808 (both MDA-MB-231): same no-primary panel e.
- AGXT PA5-142433 / Biglycan PA5-18606 (both HepG2): same goat-IgG negative control image, on uploads
  stamped 2023-01-04 and 2024-02-01.
- Not counted: CD100 MA5-47680 / PLXNB1 PA5-143747 share a panel, but the captions describe one
  double-staining experiment. Same target (likely legitimate): CDK6, IL1R, IRF1, RPS14, HUS1, NFkB p100/p52.
- False by eye: PA5-34401 vs PA5-49858.
- Blots (1,487 new): template scan 14 hit products, 7 unlisted:
  - **AKR1B1 PA5-118871 (pattern B, share 0.85): confirmed.** Stamped 2021-09-23. Raw-pixel lane texture
    correlates with the GRB14 and TSEN54 pattern B exemplars at r = 0.59 and 0.62, peak at zero shift
    (flipped controls 0.20 and 0.04). Not in Richardson's lists.
  - MRPL39 PA5-50062 and Mimecan PA5-148614 (pattern B, share 0.29 and 0.26): false, different layouts.
  - PA5-12546, PA5-52199, PA5-71514 (pattern C) and PA5-81963 (D): false; shift-correlation peaks 0.05,
    at the noise level and off zero.
  - Pattern A detector: 3 hits, all listed.

Forty-seventh batch (31,124 figures, 68,196 panels; crawl at ~70,760 MA5/PA5 pages):
- The ASC / MDA5 group (captions already disagree: MCF7 vs A549) adds a third ASC product, PA5-27715, whose
  caption says HeLa and MCF7 (stamped 2020-10-20).
- Retinoblastoma protein (MA5-32103, MA5-11387, PA5-27215) / RIPK2 PA5-34808 (all MCF7, stamped 2020-08-24) /
  CPT1A PA5-76788 (MCF7, stamped 2020-11-30): same no-primary panel, on uploads three months apart.
- New same-day pairs with consistent captions (plausible batch controls): p53 PA5-17648 / beta-catenin
  PA5-77933 (MCF7, 2022-03-01); HADHA PA5-76718 / FASN PA5-22111 (Hep G2, 2020-08-24); EWSR1 MA5-35826 and
  MA5-34868 / PGR PA5-94983 (T-47D, 2023-03-16); RSK1 PA5-90646 / PLCG1 PA5-86198 (NTERA-2, no stamps).
- The HeLa RAN group adds PPM1A PA5-29275 (stamped 2019-03-19) and HSP40 PA5-17382 (no stamp).
- The GAPDH / HSPE1 group adds HSPE1 PA5-96675 and PA5-79415; the SOX11 / CrkL / PRKAR1B group adds a third
  CrkL product, PA5-88241; the citrate synthase / MAOB / GSTM1 group adds citrate synthase PA5-76803.
- Same target (likely legitimate): ASC, TMEM132A, TCF7.
- False by eye: published-figure panels (MA5-12272 vs PA5-79532, PA5-49403 vs PA5-53106, PA5-34401 vs
  PA5-21759) and 5 dark non-hub pairs.
- Blots (2,305 new): template scan 20 hit products, 2 unlisted, both false by eye: PA5-85269 (pattern C,
  share 0.17) and PA5-52431 (pattern D, share 0.33) use different figure layouts from the templates.

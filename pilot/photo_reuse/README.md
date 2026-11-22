# Reused photographs: mouse bioluminescence and cell-culture images

Search for the same photographic region shown twice in one paper (same
figure or different figures), for two image types the user asked about:
mouse bioluminescence images and cell-culture micrographs (wound healing,
scratch, transwell).

- `photo_dupes.py` — the matcher. No panel detector: keypoints inside
  photo-like regions, each figure matched against itself and the paper's
  other figures, plain and mirrored, any scale 0.33–3 and rotation. Each
  hit carries `ncc`, the pixel correlation after alignment; hits under
  0.5 are repeated textures (bench pads, cage bars, panel grids) and are
  dropped at triage.
- `scan.py` — runs it over a shuffled Europe PMC result list, figures
  from the PMC open-data bucket, only figures whose caption matches the
  topic; figures are deleted again unless the paper has a hit.
- `triage.py`, `ctx.py` — contact sheets of hits, and wide-context views
  with captions for chosen hits. `rescore.py` re-runs the matcher on
  papers that had hits.

A hit only says two regions show the same pixels. Each is read against
panel labels and caption and binned (same sample / presented as
different samples / unclear) before anything goes to review.

Two standing rules from the user's audit of round 2 (21 Nov):

1. **Every item sent to review carries an argument for why the two
   images should not be the same**, read from the panel labels, the
   caption and, where those do not settle it, the main text (Methods,
   the paragraph citing the figure). `paper_text.py PMCID --fig N --grep
   REGEX --cache DIR` prints those parts of the article XML.
   `make_packet.py` refuses an item without a `why`, and the review page
   shows it under the label ("Why these should be different images").
2. **The box drawn is the whole duplicated area**, not the bounding box
   of the matched keypoints (the user's example: PMC7370327, where the
   keypoint box covered about a fifth of the overlap). `photo_dupes.
   full_extent` moves one image onto the other and pushes each side of
   the box outwards strip by strip while the fine detail still agrees;
   new scans store the result as `afull` / `bfull`. It stops at edited
   areas (it boxes where the images agree) and it cannot separate
   look-alike panels in a grid, so every box is still checked by eye and
   can be given by hand (`pairs` in the packet spec; see `PMC8201856/`).

Check on planted copies (one photo region pasted into a blank image at
0.9× and mirrored): both found, 192 and 318 inliers.

Topics: `bli` = "bioluminescence imaging" AND (mice OR mouse), 15,356
open-access papers; dark regions kept. `cell` = wound healing / scratch /
transwell assay papers; dark-background (fluorescence) regions dropped,
because merged and single-channel panels of one field match each other.

Not covered yet: edits inside a single image (erased or cloned cells,
painted signal). This finds reuse only, including one mouse photograph
under two different signal overlays.

## Pilot, 300 papers per topic (20 Nov)

**Bioluminescence:** 20 papers with a match, 37 matches, 29 with ncc ≥
0.5. None reportable. Most are one field shown as single-channel and
merged fluorescence panels, or a zoomed inset. The three mouse-image
matches are the same sample by the captions: PMC2988989 (Fig 1 cTnT and
Fig 2 AAV-6 are the same vector and capsid), PMC12239283 (one panel is
both "BALB/c" and "IV"; both rows are BALB/c injected IV), PMC11789939
(same mice at two labelled exposures).

**Cell culture:** 14 papers with a match, 21 matches with ncc ≥ 0.5.
Noise: publishers storing a colour and a print version of each figure
(`_OC` / `_PB`), extra copies named `Figa`…, correction notices carrying
old and new figures, insets, phase/merge panels. Two sent to review
(`cell_review1_key.json`, page `cell_image_reuse_round1.html`):

- PMC13258865 Fig 7: the 0 h scratch image is one photograph for
  untreated, HA and Se/HA NP; only the drawn wound outlines differ.
- PMC13297086 Fig 4G / Fig 5G: the "oe circCIAO1(5)" invasion image is
  the "NT" control image of the other figure, 5% larger.

Verdict so far (`cell_review1_results.json`): PMC13258865 is legitimate
reuse of the control image (user). Rule taken from this: one 0 h /
starting image shared by the conditions of a scratch assay is the same
sample and is not sent to review.

## Cell culture, papers 300–1,500 (21 Nov)

1,500 papers so far, 53 matches with ncc ≥ 0.5 after dropping stored
duplicates. Most are not reportable: single-channel/merge panels, phase
and merge, insets, schematics with repeated clip-art, consecutive time
points of one field, correction notices (PMC13015173, PMC12370780,
PMC12884613, PMC12775083), a shared 0 h scratch image (PMC10074231,
PMC11908088, PMC12736314; overlapping 0 h fields in PMC12911705), and a
control shared by two figures that list the same conditions (PMC8075232,
PMC8657689).

Six sent to review (`cell_review2_key.json`, page
`cell_image_reuse_round2.html`, built with `make_packet.py`):

| Paper | What |
|---|---|
| PMC12775211 | transwell blocks: Fig 3F Invasion = Fig 7C Migration with different treatments; Fig 1D Invasion = Fig 2F Migration |
| PMC12028320 | Fig 7: "Vector 48 h" scratch image identical for T98G and U87MG |
| PMC9410314 | Fig 1 SEM: (E) Exo-5-FU is the mirror image of (D) Exo-PAC |
| PMC13079295 | Fig 5 rat wound photos: day 7 panel is the day 3 scene, 20% larger |
| PMC12372785 | Fig 9E: Ctrl and si-CDH1 200X fields overlap |
| PMC7370327 | Fig 5: "blank" and "negative" transwell fields overlap |

## Bioluminescence, papers 300–1,500 (21 Nov)

1,500 papers so far. New in 300–1,500: 97 matches with ncc ≥ 0.5; 47
are fluorescence panels (dropped at triage with `GREY=1`, which keeps
only regions with bright unsaturated pixels), 50 viewed. Not reportable:
photograph and overlay of one animal, luminescence and fluorescence of
one plate, same animal over minutes, exposure variants, review articles
reprinting figures (PMC13143736, PMC3326720, PMC7883342), a protocol
illustration (PMC8273408), blank/zero-dose control columns shared by two
blocks (PMC11768954), and false matches on animals lying alike in a
holder (PMC13148951) or left-right symmetric gel lanes (PMC12485097).

One sent to review (`bli_review1_key.json`, page
`bioluminescence_reuse_round1.html`): PMC8201856 Fig 5b. The mice in the
D14 panels of two groups match the D0 panels of the same groups, and
three D7 panels match D0 panels of the neighbouring groups.

## Round 2 audit and follow-ups (21 Nov)

User's verdicts (`cell_review2_results.json`): all six are the same
image shown as different samples (PMC12775211, PMC12028320, PMC9410314,
PMC13079295, PMC12372785, PMC7370327). PMC12028320 was first marked
acceptable ("Vector is usually the control"); after I pointed out that
the two panels are headed T98G and U87MG and the Methods name separate
T98G-vector and U87MG-vector lines, the user changed it to a real
duplicate. Rule taken from this: a control image shared between two
cell lines is not a shared control.

The round 2 page was rebuilt with whole-area boxes and an argument per
item (same file name; the verdicts above stand).

- `PMC13079295/`: all three wound photographs (day 3, 7, 14) are one
  photograph; the wound is cut shorter from one end (3.3, 2.2, 0.9 cm)
  and the fur smoothed in B and C; C is also stretched.
- `PMC8201856/`: panel-by-panel comparison of the 15 mouse panels. Four
  pairs are the same photograph. This corrects the first version of the
  bioluminescence round 1 page, which claimed a fifth pair that is not a
  match.

Bioluminescence round 1 verdict (`bli_review1_results.json`): PMC8201856
confirmed by the user as real reuse (21 Nov).

## Cell culture, papers 1,500–2,700 (21 Nov)

2,700 papers so far. 34 new matches with ncc ≥ 0.5. Not reportable:
schematics and tables, insets, single-channel/merge, raw and annotated
copies of one image (PMC9513113), one control for short- and long-term
series with a single control bar (PMC11641017), before/after of one
field, controls shared by two dilution figures (PMC11889099).

Six sent to review (`cell_review3_key.json`, page
`cell_image_reuse_round3.html`), each with its argument:

| Paper | What |
|---|---|
| PMC12139281 | Fig 2: "0.0 nM DEXA" and "10 nM DEXA" are one field |
| PMC10006185 | Fig 2D: "shCtrl, no 5-FU" = "shCRYAB #1, + 5-FU" |
| PMC12447747 | Fig 7B "HIF-1a" = Fig 9B "TCF12 sh + HIF-1a" |
| PMC13485777 | Fig 4: Lectin image contains the Control image turned 180° |
| PMC12658732 | Fig 7: si-NC = OE-NC (weaker: both negative controls) |
| PMC11679756 | Control in Fig 2C = Control in Fig 5B (unclear: maybe shared) |

Round 3 verdicts (`cell_review3_results.json`): five of six are the same
image shown as different samples (PMC12139281, PMC10006185, PMC12447747,
PMC13485777, PMC12658732). PMC11679756 is acceptable: "Even though the
experiments are different it's technically possible they could have the
same control". Rules taken from this: an untreated control of one cell
line shared between two figures is not sent to review, even when the
figures are different experiments; negative controls for different
reagents (si-NC and OE-NC) shown as one image are reportable.

Confirmed so far in cell-culture figures: 11 papers from 2,700
(round 2: six; round 3: five). Round 1: PMC13258865 acceptable,
PMC13297086 awaiting a verdict.

## Bioluminescence, papers 1,500–2,700 (21 Nov)

2,700 papers so far. New: 115 matches with ncc ≥ 0.5, 50 of them
fluorescence panels (dropped), 65 viewed. Not reportable: grids of
animals in one holder that only look alike (PMC6796468 NC vs KD mice
differ on viewing; the match was the stage pattern), the same animal
over time or under two probes, photograph and overlay, single-channel
and merge (PMC9459417 EdU), review articles, schematics and tables.

Two sent to review (`bli_review2_key.json`, page
`bioluminescence_reuse_round2.html`):

- PMC10874017 Fig 9B: in the NS row the second and fifth mouse are one
  image (pair score 0.98; other 65 pairs ≤ 0.86, median 0.73). Same
  group, so one animal shown twice.
- PMC6804745 Fig 3e (histology): "TRAP, Zoledronic acid" is the same
  image as "TRAP 2, Denosumab".

Bioluminescence round 2 verdicts (`bli_review2_results.json`): both
confirmed as real duplicates (PMC10874017, PMC6804745). The user's note:
both may be mistakes rather than deliberate. Nothing in the images
settles intent either way: each is an unaltered copy placed once, with no
rotation, mirroring, cropping or retouching, which is what a layout slip
looks like; the scan cannot tell that from deliberate reuse.

## Cell culture, papers 2,700–3,900 (21 Nov)

3,900 papers so far. 37 new matches with ncc ≥ 0.5. Not reportable:
schematics, charts, insets, single-channel/merge, a "0 h original
injury" reference image declared in both captions (PMC11540258), SEM
instrument bars (PMC12805422), same field over time.

Five sent to review (`cell_review4_key.json`, page
`cell_image_reuse_round4.html`):

| Paper | What |
|---|---|
| PMC12274886 | Fig 5A: "Vector" = "MNAT1-OE + GDF15-KD" transwell image |
| PMC10890652 | Fig A3: the three 72 h images are one image, mirrored / flipped |
| PMC13481467 | Fig 5E: NC+LPS = OE-Vector+LPS, turned ~107° |
| PMC13412505 | Fig 8 rat wounds: Gel 75 mg = Gel 100 mg on day 0 and day 3 |
| PMC11866248 | Fig 9B: Migration 100 µM and Invasion 100 µM overlap, turned ~140° (weaker) |

## Bioluminescence, papers 2,700–3,900 (21 Nov)

3,900 papers so far. 88 mouse-image matches viewed (fluorescence panels
dropped). Not reportable: photograph and overlay, same animal over
minutes or under two probes, a representative image repeated in an
Extended Data figure under the same label (PMC7136154), stage and
holder patterns, look-alike pairs that differ on viewing (PMC11004311),
review articles, schematics.

Two sent to review (`bli_review3_key.json`, page
`bioluminescence_reuse_round3.html`):

- PMC9239262 Fig 4B: the day 28 row is the day 14 row for all three
  groups, signal included (panel scores 0.91, 0.98, 0.97; day 3 against
  either 0.23–0.47).
- PMC12818144 Fig 4A: the 6 h image of one group is the 24 h image of
  another group, animal and signal.

Round 4 verdicts (`cell_review4_results.json`): all five confirmed by
the user. Confirmed in cell-culture figures so far: 16 papers from 3,900.

Bioluminescence round 3 verdicts (`bli_review3_results.json`): both
confirmed by the user (PMC9239262, PMC12818144). Confirmed from the
bioluminescence scan so far: 5 papers from 3,900 (PMC8201856,
PMC10874017, PMC6804745, PMC9239262, PMC12818144); PMC6804745 is
histology in a matching figure, not a mouse image.

## Bioluminescence, papers 3,900–5,100 (21 Nov)

5,100 papers so far. 59 mouse-image matches viewed. Not reportable:
photograph and overlay rows (PMC10859097: PBS and treated animals
score 0.73–0.88 against each other, the photo/overlay pairs 0.97–1.00),
same animal over minutes or under two probes, grids of look-alike
animals, schematics and tables, review articles.

Two sent to review (`bli_review4_key.json`, page
`bioluminescence_reuse_round4.html`):

- PMC10734064 Fig 1B / Fig 2B: the same six liver photographs and H&E
  sections for two different tumour cell-line models.
- PMC10968997 Fig 2: the day 21 and day 28 panels are one photograph of
  the animal under two different signals.

## Cell culture, papers 3,900–5,100 (21 Nov)

5,100 papers so far. 27 new matches with ncc ≥ 0.5. Not reportable:
schematics, insets, single-channel/merge, raw and annotated copies,
shared 0 h scratch images (PMC11585646), untreated control rows shared
between figures (PMC10743841 Fig 6/8 and 7/9), a correction-style repeat
(PMC11662515 Fig 2/6 controls).

Three sent to review (`cell_review5_key.json`, page
`cell_image_reuse_round5.html`):

| Paper | What | Copy |
|---|---|---|
| PMC8176915 | Fig 4: si-NMU (C) = si-NTS (F) transwell field | turned ~75°, re-cropped, recoloured |
| PMC12657826 | Fig 6: 48H image identical for CPC and 5%PVA/CPC | plain |
| PMC10743841 | Fig 6: DMM-11 row, 24 h (f) = 48 h (j) | plain |

Round 5 verdicts (`cell_review5_results.json`): all three confirmed by
the user. Confirmed in cell-culture figures so far: 19 papers from 5,100.

## Bioluminescence, papers 5,100–6,300 (21 Nov)

6,300 papers so far. 72 mouse-image matches viewed. Not reportable:
photograph and overlay or two-probe views of the same animals
(PMC7810895, PMC6828332, PMC6896159, PMC12187574), raw and ROI-annotated
copies (PMC6201850, caption says so), one animal imaged through two
emission filters in a mixed infection (PMC6853927 Fig 8), the same
session shown in two figures with different ROIs (PMC5762894), grids of
look-alike animals, the imaging stage matching itself (PMC5581022).

`panel_pairs.py FIGURE spec.json` scores every pair of named panels on
the greyscale photograph only (colour overlay masked), best over small
shifts and scales; used below to show that a pair stands out from the
other panels of its figure.

Four sent to review (`bli_review5_key.json`, page
`bioluminescence_reuse_round5.html`):

| Paper | What | Pair score vs rest of figure |
|---|---|---|
| PMC5090211 | Fig 2: rat at 40 min (A), 3 days (B), 5 days (C) is one photograph | B/C 0.97, A/B 0.91 |
| PMC6047774 | Fig 1B, day 0: Infected = Infected + Mupirocin (weaker: pre-treatment day) | 0.86 vs ≤ 0.76 |
| PMC6244358 | Fig 9, blue light alone: day 1 = day 3, day 2 = day 4 | 0.89, 0.94 vs ≤ 0.82 |
| PMC3836995 | Fig 7B dorsal: day 1 = day 14 photograph, different signal | 0.87 vs 0.56 |

All four are plain copies of the photograph; the overlay differs in
three of them.

## Cell culture, papers 5,100–6,300 (21 Nov)

6,300 papers so far. 34 new matches with ncc ≥ 0.5. Not reportable:
schematics, insets and magnified views, analysis overlays, untreated
control row shared between figures (PMC12892515 Fig 8/9/10, PMC10605247
Fig 8/9), shared 0 h column (PMC12231746), one tissue shown as both
"normal" and "Gb3 negative" example (PMC12917973).

Five sent to review (`cell_review6_key.json`, page
`cell_image_reuse_round6.html`):

| Paper | What | Copy |
|---|---|---|
| PMC6360294 | Fig 4C: UMUC-NC 12 h = UMUC-siRNA 24 h scratch image | plain |
| PMC11763410 | Fig 3G HN30 IR plate = Fig 6B 090RR 4 Gy plate | plain, resized |
| PMC11536251 | Fig 2D: siFMRP-2 and siFMRP-3 are overlapping crops of one field | shifted crop |
| PMC12852651 | Fig 6b: BCSC YAP1 siRNA 0 h = 24 h (could be the same field re-photographed) | plain or re-imaged |
| PMC7718642 | Fig 4a: ACHN = H-NC transwell image (two controls) | plain |

## Bioluminescence, papers 6,300–7,500 (21 Nov)

7,500 papers so far. 72 mouse-image matches viewed. Not reportable:
main figure and its figure supplement (PMC6021173), one experiment shown
in a main and an expanded-view figure (PMC10565638), photograph and
overlay or two modalities of the same animals (PMC5333872, PMC10898324,
PMC7248428, PMC13255310), the 24 h row repeated in a comparison panel
(PMC8474941), one animal followed over minutes or light doses
(PMC4491820, PMC7064570, PMC9315199), control column shared between two
figures (PMC7886131), layout or imaging stage matching itself
(PMC5200896, PMC10308360, PMC12936002, PMC12049435, PMC5744014 where all
panels are X-ray views in one holder, best pair 0.81).

Sent as `bioluminescence_reuse_round6.html`, key `bli_review6_key.json`:

| id | paper | match |
|---|---|---|
| B36 | PMC9688407 | Fig 7A: CTL mice 2–3 = TMZ mice 2–3, signal included (0.96; other groups 0.79) |
| B37 | PMC5876459 | Fig 3B transwell: Hepa1-6 = Hepa1-6-FLuc turned 36° (132/137 points on one rotation) |
| B38 | PMC7312797 | Fig 5A: Group A 21 d = Group B 28 d photo (0.84; others < 0.40); Fig 5B control hMito = control OCN nuclei |

## Cell culture, papers 6,300–7,500 (22 Nov)

7,500 papers so far. 33 new matches with ncc ≥ 0.5. Not reportable:
schematics, shared 0 h scratch image (PMC11492136 Fig 2, PMC12937787,
PMC12655155), control shared between two figures on one cell line
(PMC12024059, PMC12130024, PMC7529912), one well followed over time
(PMC12346839), one tissue overview with different ROIs (PMC12050407), a
correction notice printing its figure twice (PMC11980132), a paper
already retracted (PMC11670366).

Sent as `cell_image_reuse_round7.html`, key `cell_review7_key.json`:

| id | paper | match |
|---|---|---|
| T08 | PMC11492136 | Fig 6D invasion = Fig 6E migration for Reg+RRM2, both cell lines (0.90 each; others < 0.12) |

## Bioluminescence, papers 7,500–8,700 (22 Nov)

8,700 papers so far. 63 mouse-image matches viewed. Not reportable:
one session shown at two colour scales (PMC3743513, caption says so),
the same mouse or lungs repeated across figures as "the same mice"
(PMC11259842, PMC3527494), control row shared between two cohorts
figures (PMC4924861), photograph beside overlay or two modalities
(PMC6401411, PMC10288272, PMC12843090, PMC13454112), single-channel and
merge (PMC6505074 Fig 3), renderings and schematics (PMC3426305,
PMC10196834), figure stored twice (PMC11366154, PMC12285008), grids of
look-alike animals.

Sent as `bioluminescence_reuse_round7.html`, key `bli_review7_key.json`:

| id | paper | match |
|---|---|---|
| B39 | PMC10976084 | Fig 7: G3 (training) = G5 (omega-3) at day 14 and day 21, signal included (0.90, 0.99; figure median 0.78) |
| B40 | PMC4454195 | Fig 7: control A day 0 = D day 12 photograph, different overlay (0.92; others ≤ 0.75) |
| B41 | PMC6505074 | Fig 9b IHC control: p-AKT = β-catenin field, shifted crop |

## Cell culture, papers 7,500–8,700 (22 Nov)

8,700 papers so far. 50 new matches with ncc ≥ 0.5. Not reportable:
insets and magnified views, schematics, single channel and merge, raw
and analysed copies, colour and print versions of one figure
(PMC11141472 `_OC`/`_PB`), a correction notice (PMC12538872), control
plates shared between two figures on one cell line (PMC12531794, the
Control and Mimic plates of Fig 4 reappear in Fig 5), overlapping
columns matching themselves (PMC10531673, PMC10453269).

`region_match.py` fits one similarity transform between two
regions with SIFT, also trying the mirror image, and reports inliers,
scale, rotation and shift; used for the numbers below.

Sent as `cell_image_reuse_round8.html`, key `cell_review8_key.json`:

| id | paper | match |
|---|---|---|
| T09 | PMC9279021 | Fig 2c (Rac1 overexpression) = Fig 3c (si-Rac1), whole wound-healing block |
| T10 | PMC13465012 | Fig 4: Ctrl 24 h = 100% DM 24 h (717/718) |
| T11 | PMC11141472 | Fig 5e MCF-7: Control plate = miR-1296-5p(+)+TRIM14(+) plate turned 90° |
| T12 | PMC12650368 | Fig 2: U-2 OS grid (A) = MCC26 grid (G), all rows |
| T13 | PMC8258952 | Fig 2A: 25 µM NDP = 25 µM DHM, shifted crop (182/183) |
| T14 | PMC8629617 | Fig 1a: 2.5% TSW = 5% TSW, shifted crop (208/213) |
| T15 | PMC6738998 | Fig 4 MCF-7 4 µg/mL: invasion = migration turned 90° (77/77) |
| T16 | PMC11699557 | Fig 2: (d) = (e) (145/150) |
| T17 | PMC10227323 | Fig 4B: B-group field = C-group field mirrored (70/72), low resolution |
| T18 | PMC11294307 | Fig 3E: 'cell' = ov-NC, both lines (two controls) |
| T19 | PMC6408831 | Fig 3a: Control = NC, shifted crop (two controls) |

## Bioluminescence, papers 8,700–9,900 (22 Nov)

9,900 papers so far. 81 mouse-image matches viewed; none sent. Not
reportable: one animal followed over seconds or minutes (PMC1991622,
PMC8198274, PMC3715762, PMC8779867, PMC3520978), same animals under two
reporters or two modalities (PMC11675005, PMC4688563, PMC12262087,
PMC12845254 Fig 7/8, PMC4967900), an illustrative inset repeated in a
later figure (PMC4153648 Fig 2B inset = Fig 4A), control cohort shared
between figures (PMC12945804), raw and annotated copies, schematics.
Scored panel by panel and not standing out: PMC4030865 Figs 2–4 (best
pair 0.67, typical 0.55–0.62), PMC8619421 Fig 1B (0.77–0.82, all three
groups alike: stage and holder), PMC3230016 (dorsal/ventral, stage only).

## Cell culture, papers 8,700–9,900 (22 Nov)

9,900 papers so far. 54 new matches with ncc ≥ 0.5. Not reportable:
schematics, insets and zooms, raw and analysed copies, single channel
and merge, control column shared between two figures on one cell line
(PMC13203602, PMC11280071). Left out as ambiguous: PMC9416381 Fig 12
(CBD vs CBG panels match on faint marks in near-empty fields; could be
dust on the optics). PMC13100028 is the correction notice for
PMC12852651 (T06): it reprints the original Fig 6 and only moves a
label row, so the BCSC YAP1 siRNA 0 h / 24 h match is not addressed.

Sent as `cell_image_reuse_round9.html`, key `cell_review9_key.json`
(numbers from `region_match.py`):

| id | paper | match |
|---|---|---|
| T20 | PMC11514663 | Fig 3F HCC-LM3 Control = Fig 4F HUH-7 PA turned 10° (203/213); also overlaps Fig 3F HUH-7 Control (87/108) |
| T21 | PMC10688045 | Fig 1E NC-FLS ISO invasion = Fig 6E CIA-Veh invasion (274/276, 9% larger) |
| T22 | PMC13362964 | Fig 8: TFE200 72 h = TFE500 72 h (185/186) |
| T23 | PMC12482102 | Fig 3B: Control siRNA 24 h = CASC19 siRNA 48 h (59/60) |
| T24 | PMC12239490 | Fig 7c tube formation: Control = CM+anti-CXCL12 (223/225) |
| T25 | PMC10639105 | Fig 7A mimic+Fedratinib: migration = invasion (192/193) |
| T26 | PMC7485740 | Fig 2C SK-BR-3 Leptin = Fig 4A Leptin+SDF-1, 20% larger (156/161) |
| T27 | PMC13397375 | Fig 2G oe-miR-NC: S18 = 5-8F, shifted crop (93/105) |
| T28 | PMC12481119 | Fig 5A IHC, KRAS WT: KRAS stain = Ki67 stain, shifted (102/106) |
| T29 | PMC7930260 | Fig 7A: Blank = NC, shifted crop (545/563; two controls) |

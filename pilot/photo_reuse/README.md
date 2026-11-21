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

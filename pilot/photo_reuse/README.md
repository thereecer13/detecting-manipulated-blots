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

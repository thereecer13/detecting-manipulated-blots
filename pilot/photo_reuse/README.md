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

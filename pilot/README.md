# Pilot: Claude judging blots blind, in-session (no API credits)

Run 2026-11-06 inside a Claude Code session. Each batch of 10–15 items went to a separate
sub-agent that saw only hashed image files: a grayscale copy (long side 512 px) and one or
more processed views of it (see "Image views" below). The prompt stated the base rate (about half) for BioFors. Judges
could only look at the images with the Read tool: no code, and no other files. Labels sat
in a separate folder they were not told about. The judges ran on the session's model;
model and effort level were not pinned, unlike in an API run.

- `build_pilot.py` builds the sets, and `views.py` makes the processed views.
- `score_pilot.py <scratch dir> runs/<run>` scores a run.
- `sheets.py` draws the review sheets of errors. It uses `rich_ann.py` to find Richardson's
  annotation files, whose names don't always match the spreadsheet.
- `labels.json` holds the hidden labels; `runs/` holds the answers for each run.
- Images are not committed. Rebuild them with `build_pilot.py` from the BioFors archive
  and Richardson Zenodo version `260605`.

## Image views

**Runs 1 and 2.** The "contrast-stretched" copy mapped the median-to-99.5th-percentile
range to black-to-white. That pushed more than half of every image to pure black, including
the bands and the darker half of the background. On vendor images with near-white
backgrounds, 95% of pixels were clipped, even after the run 2 patch.

**Run 3 onwards** uses three views, computed at the image's native resolution (`views.py`):
- **Equalized:** global histogram equalization. The common background gray levels get most
  of the range, like Richardson's black-point/white-point adjustment, but without clipping.
- **Local contrast:** CLAHE, which boosts texture region by region.
- **Noise residual:** the image minus a Gaussian blur (sigma 1.5), centred on mid-gray.

At most a median of 2% of pixels are newly clipped in any view, apart from the residual's
band edges. The judge prompt describes each view and the artifacts it can show: JPEG
blocks, posterization contours and residual halos.

## Results

| set | n | F1 | precision | recall | AUC (95% CI) |
|---|---|---|---|---|---|
| A. single blot, BioFors (IDD/CSTD vs unflagged papers) | 30 + 30 | 0.62 | 0.61 | 0.63 | 0.70 (0.56–0.82) |
| B. blot pair, BioFors (EDD pairs vs same-paper pairs) | 15 + 15 | 0.80 | 1.00 | 0.67 | 0.92 (0.81–1.00) |
| Richardson within-blot positives, recall only, run 1 | 20 | — | — | 0.35 | — |
| Richardson, run 2 (patched stretch + one hint about flat backgrounds) | 20 | — | — | 0.35 | — |
| **Run 3, fixed views:** A. single blot, BioFors | 30 + 30 | 0.63 | 0.71 | 0.57 | 0.71 (0.58–0.84) |
| **Run 3:** B. blot pair, BioFors | 15 + 15 | 0.75 | 1.00 | 0.60 | 0.92 (0.81–0.99) |
| **Run 3:** Richardson, recall only | 20 | — | — | **0.60** | — |

**What the fixed views changed**
- **Richardson:** recall went from 7/20 to 12/20. Run 3 caught 6 that run 1 missed and
  missed 1 that run 1 caught; 14/20 were caught in at least one run. With no clean vendor
  images, we can't tell whether part of this gain is just more readiness to flag vendor
  images.
- **BioFors:** no real change. Single-blot F1 went from 0.62 to 0.63, with fewer false
  alarms (12 to 7) but more misses (11 to 13). Pairs went from 0.80 to 0.75 (one more miss).
- **Run-to-run noise is large:** 15 of 60 single-blot verdicts changed between runs 1 and 3
  while F1 stayed flat. The main experiment needs repeated runs, or averaged
  probabilities, to see effects smaller than about 0.1.

### Run 1 details

**Task A details**
- Recall was 17/24 on splices (CSTD) but only 5/11 on duplications within an image (IDD).
- 13 of 19 true positives pointed at a ground-truth box (IoU ≥ 0.1).
- The 12 false alarms were spread evenly: 4 "splice", 4 "duplication", 4 "painting".
- Most misses got p = 0.40–0.45 with a stated suspicion that the judge then didn't act on.

**Task B details:** no false positives. The 5 missed pairs were partial overlaps, with
p = 0.05–0.40.

**Richardson details**
- Each run caught 7/20, but they agreed on only 5; 9/20 were caught at least once.
- Painted backgrounds were mostly missed.
- With no clean vendor images (the Thermo Fisher site blocks this cloud machine),
  precision can't be measured here.

## Problems with this pilot

- **Contrast-stretch bug** (runs 1 and 2): see "Image views" above. Fixed in run 3.
- **Assay mix.** No western-only filter was applied, so some BioFors items are gels.
- **Contrast shortcut.** Image contrast alone separates the task A classes somewhat
  (std AUC 0.31).
- **Small sample.** With n this small, every interval is wide.

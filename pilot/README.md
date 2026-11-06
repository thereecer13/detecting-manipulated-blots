# Pilot: Claude judging blots blind, in-session (no API credits)

Run 2026-11-06 inside a Claude Code session. Each batch of 10–15 items went to a separate
sub-agent that saw only hashed image files: a grayscale copy (long side 512 px) and a
contrast-stretched copy. The prompt stated the base rate (about half) for BioFors. Judges
could only look at the images with the Read tool: no code, and no other files. Labels sat
in a separate folder they were not told about. The judges ran on the session's model;
model and effort level were not pinned, unlike in an API run.

- `build_pilot.py` builds the sets, and `score_pilot.py` scores them.
- `labels.json` holds the hidden labels; `judgments/` holds the answers.
- Images are not committed. Rebuild them with `build_pilot.py` from the BioFors archive
  and Richardson Zenodo version `260605`.

## Results

| set | n | F1 | precision | recall | AUC (95% CI) |
|---|---|---|---|---|---|
| A. single blot, BioFors (IDD/CSTD vs unflagged papers) | 30 + 30 | 0.62 | 0.61 | 0.63 | 0.70 (0.56–0.82) |
| B. blot pair, BioFors (EDD pairs vs same-paper pairs) | 15 + 15 | 0.80 | 1.00 | 0.67 | 0.92 (0.81–1.00) |
| Richardson within-blot positives, recall only, run 1 | 20 | — | — | 0.35 | — |
| Richardson, run 2 (fixed stretch + one hint about flat backgrounds) | 20 | — | — | 0.35 | — |

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

- **Contrast-stretch bug.** The stretch came out all black on images with pure-white
  backgrounds: 6/60 task A images, 10/60 pair images and 13/20 Richardson images. Only
  Richardson was re-run with the fix.
- **Assay mix.** No western-only filter was applied, so some BioFors items are gels.
- **Contrast shortcut.** Image contrast alone separates the task A classes somewhat
  (std AUC 0.31).
- **Small sample.** With n this small, every interval is wide.

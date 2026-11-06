# Test 3: rulebook v2 vs v1 vs no rules (blind, fresh images)

Run 2026-11-06, in-session (no API credits). The rules are in `rules/v1.yaml` and
`rules/v2.yaml`; v2 was frozen and committed before this test. Set builder:
`pilot/build_test3.py`. Scorer: `pilot/score_test3.py`.

## Set

- **BioFors:** 30 manipulated blots (IDD/CSTD) from 13 papers not used in the pilot or
  test 2. These are the last usable ones, all thin strips (median 347×33 px, minimum side
  25 px). They are paired with 30 clean blots matched to them on height and aspect ratio.
  Image size carries no signal (AUC 0.50), but contrast still does a little (std AUC 0.34).
- **Richardson:** 30 manipulated images from the August 2026 release, not used before:
  15 "painting" and 15 other within-blot problems, from 7 vendors. Two turned out to be
  immunofluorescence panels (no western filter was applied), so they are left out of
  recall, which is over 28.
- Every condition saw the same 7 batches, with a separate sub-agent per batch. All saw
  the same four files per image.

## Results

| condition | F1 | precision | recall | false positives (of 30 clean) | AUC | IDD | CSTD | Richardson: painting | Richardson: other |
|---|---|---|---|---|---|---|---|---|---|
| no rules | **0.71** | **0.72** | **0.70** | **8** | **0.79** | 5/10 | 18/22 | 1/13 | 0/15 |
| rulebook v1 | 0.61 | 0.59 | 0.63 | 13 | 0.70 | 5/10 | 15/22 | **4/13** | **1/15** |
| rulebook v2 | 0.68 | 0.66 | **0.70** | 11 | 0.77 | 5/10 | 18/22 | 3/13 | 0/15 |

- **F1 intervals:** the 95% bootstrap interval, resampling papers, is about ±0.15.
- **Paired comparisons with no rules on BioFors:**
  - v1 fixed 4 verdicts and broke 11 (McNemar p = 0.12);
  - v2 fixed 6 and broke 9 (McNemar p = 0.61).

## What happened

- **v2 recovered most of v1's loss** (F1 0.61 → 0.68), but did not beat no rules (0.71).
- **The clearing rules worked as intended.** v2 cleared 2 clean blots that no-rules
  flagged; both were read as disclosed splices or ordinary lane gaps.
- **The new flag rules caused false alarms on thin strips.** "Bands should follow the
  gel's shape" and "each lane should have the same grain" flagged 6 clean blots that
  no-rules had cleared, all 25–40 px tall, where lane-to-lane variation looks like jumps
  or grain changes.
- **The disclosed-splice rule was sometimes misapplied.** 2 manipulated blots were
  cleared because a seam was read as a "drawn separator" (41ff7f5009, d48095670e).
- **Recall on vendor images was very low in every condition** (1–5 of 28), far below the
  June-release images in the pilot (12/20 in run 3). Judges often called flat vendor
  backgrounds "this vendor's typical processing". The v2 rule "a background flat
  everywhere is contrast adjustment" points the same way. Without clean vendor images,
  we can't tell whether that judgment is too lenient or right.

## Across tests 2 and 3

On fresh images, no rulebook has beaten no rules yet:
- test 2: v1 as text 0.75 vs no rules 0.75;
- test 3: v1 0.61, v2 0.68 vs no rules 0.71.

The sets are small and the intervals wide, so the real effect of the rules is somewhere
between "slightly harmful" and "slightly helpful". It is not large.

## Caveats

- **Thin strips:** the BioFors positives here are the hardest images for most of the
  rules. These results say little about the rules on sharp, high-resolution blots.
- **Single judgments:** one judge per item per condition. Run-to-run noise was about 25%
  of verdicts in the pilot.
- **Shared papers:** the 30 positives come from only 13 papers.

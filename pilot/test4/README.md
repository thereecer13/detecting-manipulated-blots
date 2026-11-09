# Test 4: rulebook v3 vs v2 vs no rules (blind, fresh images)

Run 2026-11-06, in-session (no API credits). Rulebook v3 (`rules/v3.yaml`) is v2 without
the two flag rules that over-fired in test 3: "bands should follow the gel's shape" and
"each lane should have the same grain". v3 and the set builder (`pilot/build_test4.py`)
were committed before any judging. Scorer: `python pilot/score_tests.py <scratch> test4
baseline,rules_v2,rules_v3`.

## Set

- **BioFors, code-made manipulations.** BioFors has no unused real within-blot
  manipulations left. So 30 clean blots from 60 papers not used before (at least 40 px tall,
  median 286×75) were manipulated in code:
  - 10 undisclosed splices (the right part replaced by another blot from the same paper,
    with no gap);
  - 10 lane duplications (a lane-wide strip copied over another lane, half flipped);
  - 10 painted background patches (flattened to their median gray, with a soft edge).

  30 untouched clean blots from other new papers are the negatives. All 60 images were
  re-saved as JPEG at quality 85, so compression is identical. No single image statistic
  separates the classes (AUCs 0.45–0.56).
- **Richardson:** 30 unused August 2026 images (15 painting, 15 other). Two are not blots
  (a fibre micrograph and an immunofluorescence image), so recall is over 28.
- Every condition saw the same 7 batches, with a separate sub-agent per batch.

## Results

| condition | F1 | precision | recall | false positives (of 30) | AUC | splice | duplication | painting | Richardson |
|---|---|---|---|---|---|---|---|---|---|
| no rules | 0.85 | 0.86 | 0.83 | 4 | 0.92 | 10/10 | 9/10 | 6/10 | 3/28 |
| rulebook v2 | 0.81 | 0.83 | 0.80 | 5 | 0.92 | 9/10 | 8/10 | 7/10 | 4/28 |
| rulebook v3 | **0.88** | **0.93** | 0.83 | **2** | **0.94** | 9/10 | 9/10 | 7/10 | 3/28 |

- **F1 intervals:** the 95% bootstrap interval is about ±0.09.
- **Paired comparisons with no rules:**
  - v3 fixed 5 verdicts and broke 3 (McNemar p = 0.73);
  - v2 fixed 5 and broke 7 (McNemar p = 0.77).

## What happened

- **v3 is the first rulebook ahead of no rules on fresh images**: F1 0.88 vs 0.85, with half
  the false alarms (2 vs 4). The gain is in precision, as intended: the clearing rules
  cleared 4 clean blots that no-rules flagged. **The difference is not statistically
  significant.**
- **Dropping the two flag rules mattered.** v2 flagged 4 clean blots that v3 cleared
  (2c998b79cd, 1e9dc735b3, cdd8ed2417, eee7ecd31c), mostly by reading a band "jumping"
  between lanes or a change in grain as a splice. This is the same failure seen on the thin
  strips in test 3, now on taller blots.
- **Painting** was the hardest manipulation for every condition (6–7/10), because the
  patches were flattened to the surrounding gray. All three conditions caught nearly every
  code-made splice and duplication.
- **Vendor images:** recall stayed very low in every condition (3–4 of 28), as in test 3.

## Caveats

- **Code-made manipulations are not real ones.** The splices join two different blots and
  are easy, so absolute scores here overstate real-world accuracy. The comparison between
  rulebooks is the meaningful part.
- **Small sample:** 30 + 30, one judge per item per condition. Run-to-run noise was about
  25% of verdicts in the pilot. A 3-point F1 difference is within noise.
- **No vendor precision:** still unmeasured, since there are no clean vendor images.

## Re-run of the Richardson images with the fixed equalized view (2026-11-09)

The equalized view used in tests 2–4 equalized the whole figure, so on vendor figures the white
page took the bright end of the range and pushed the blot background toward black. The view now
equalizes only inside the blot panels (`pilot/views.py`). The fix changed the view substantially
for 28 of these 30 images.

The same 30 Richardson images were re-judged blind with the fixed view, under the same three
conditions and the same batches. Results are in `runs_fixed_view/`. Recall is over the 28 images
that are western blots.

| condition | old view | fixed view | painting (of 15) | other (of 13) |
|---|---|---|---|---|
| no rules | 3/28 | 6/28 | 2 → 4 | 1 → 2 |
| rulebook v2 | 4/28 | 8/28 | 2 → 5 | 2 → 3 |
| rulebook v3 | 3/28 | 7/28 | 2 → 4 | 1 → 3 |

The bug roughly halved recall on vendor images. Even with the fix, about three quarters of
Richardson's within-blot findings are still missed.

# Test 2: does rulebook v1 help? (blind, fresh images)

Run 2026-11-06, in-session (no API credits). The rules are in `rules/v1.yaml`, frozen
before this test. Measurement code: `pilot/rule_tools.py`. Set builder:
`pilot/build_test2.py`.

## Set

- **BioFors:** 30 manipulated blots (IDD or CSTD) and 30 clean blots, all from papers
  **not used in the pilot**, so nobody looked at these images while writing the rules.
- **Richardson:** 20 within-blot images not used in the pilot. These are manipulated only,
  so we measure recall only.
- All images are blind (hashed names), with the same four files per image as pilot run 3:
  the image, equalized, local contrast and noise residual.

## Conditions

Each condition had the same 6 batches, with a separate sub-agent per batch.

| condition | what the judge got |
|---|---|
| baseline | the pilot run 3 prompt, no rules |
| rules_text | + the three rules, worded as written by the biologist |
| rules_tools | + the rules, plus the measurements: band outline similarities with gray-value correlations, straight transitions, flat patches, as text and as an overlay image |
| rules alone | no Claude: "manipulated" if any rule fires mechanically |

## Results

| condition | F1 | precision | recall | false positives (of 30 clean) | AUC | IDD recall | CSTD recall | Richardson recall |
|---|---|---|---|---|---|---|---|---|
| baseline | **0.75** | **0.81** | 0.70 | **5** | 0.77 | 8/12 | 19/24 | 11/20 |
| rules_text | **0.75** | 0.76 | 0.73 | 7 | **0.81** | 8/12 | 19/24 | **13/20** |
| rules_tools | 0.64 | 0.69 | 0.60 | 8 | 0.77 | 5/12 | 17/24 | 8/20 |
| rules alone | 0.65 | 0.52 | **0.87** | 24 | — | — | — | 12/20 |

- **F1 intervals:** the 95% bootstrap interval is about ±0.12 for every condition.
- **Paired comparisons with baseline on BioFors:**
  - rules_text fixed 4 verdicts and broke 5 (McNemar p = 1.0);
  - rules_tools fixed 3 and broke 9 (McNemar p = 0.15).

## What happened

- **Rules as text** made no measurable difference to verdicts. AUC rose slightly (0.77 to
  0.81) and Richardson recall rose by 2. False positives did not go down (5 to 7).
- **Rules with measurements** made things worse, in two ways:
  1. The straight-line measurement fires on most clean blots: lane gaps, strip edges and
     band-row edges at this low resolution. Judges took several of these at face value. 5 of
     the 9 broken verdicts are clean blots with 4 to 10 detected "edges".
  2. The band-outline rule fires on many pairs whenever bands are uniform: up to 30 pairs
     at ≥ 0.95 in one image. Judges learned to discount it ("evenly loaded bands look
     alike"), and then also discounted it on truly duplicated blots. IDD recall fell from
     8/12 to 5/12.

  On Richardson images, judges given measurements more often dismissed flat backgrounds
  as "this vendor's processing" (11 to 8).
- **Rules alone** catch 87% of manipulated blots but flag 24 of 30 clean ones.

## Caveats

- Small sample (60 + 20). The baseline here (F1 0.75) is well above pilot run 3 (0.63) on
  different images, so set-to-set variation is large.
- One judge per item per condition; run-to-run noise was about 25% of verdicts in the
  pilot.
- The measurements are my implementation of the rules. A better band segmenter or line
  detector could behave differently, especially on high-resolution images.

# Blind test of the biologist's painting rule (user as judge)

Rule under test: painted backgrounds show smooth, homogeneous patches outside the bands, inside an
otherwise grainy, blotchy background.

Set: 64 test 5 blots fetched from the vendor sites through one pipeline (32 Richardson-flagged, 29
of them painting; 32 user-verified clean), original + blot-only equalized view, lossless, no labels.
Painted blots seen earlier with Richardson's annotations were excluded, so the painted set is the
32 that at least one model judge caught (easier cases; judge recall here is inflated).

| judge | F1 | precision | recall | clean called painted |
|---|---|---|---|---|
| user, all 64 | 0.69 | 0.62 | 0.78 | 15/32 |
| user, 55 decided | 0.76 | 0.62 | 0.96 | 15/29 |
| model, no rules | 0.83 | 0.92 | 0.75 | 2/32 |
| model, rulebook v3 | 0.83 | 0.82 | 0.84 | 6/32 |

User's calls track the presence of exactly flat background (median flat share: called painted 0.57,
called not painted 0.03). Decided calls beat chance (39/55, p = 0.001).

Labelled follow-up on the 15 false positives (`user_comparison.json`), each next to a caught painted blot:
- 6 "the right one also looks painted" (TA890102, TA813056, MA5-49484, TA811398, MA5-34931, TA811407);
  4 of these were also called painted by rulebook v3 in test 5. Either Richardson's list misses some
  painted images, or these are ambiguous: the 'clean' class is 'not flagged', not verified clean.
- 6 "I see a difference": mostly "could be compression"; one concrete criterion: when the smooth area
  covers nearly all of the background outside the bands it is global processing, not targeted
  painting of unwanted bands. Flat share: these 6 median 0.86, caught painted blots median 0.58, but
  8 of 24 caught painted blots are also above 0.8.
- 3 unsure.

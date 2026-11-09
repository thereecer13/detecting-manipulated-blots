# Test 5: real vendor blots (Richardson manipulated vs scraped clean)

First test where both classes are real vendor catalog images, so precision is measured on clean blots
that a biologist checked by eye.

## Set
- **Manipulated (93):** August 2026 Richardson images with a within-blot problem (no shared-template or
  cross-image finding), file name marked as a western blot, not used in tests 1-4.
- **Clean (93):** scraped from the same vendors and catalog prefixes (`scrape_vendors.py`), screened
  for duplicates and Richardson template backgrounds (`screen_scraped.py`), then reviewed by the user
  in `make_review_html.py`. Of 102 reviewed, 93 were marked clean, 8 unsure (mostly over-processed
  flat backgrounds), 1 not a western blot, 0 manipulated. Only the 93 confirmed clean were kept, each
  with its matched manipulated partner (`clean_review_results.json`).
- Pairs are matched within catalog prefix (MA5-, PA5-, RAB0, TA8, TA5) on mean brightness, white
  fraction and aspect ratio. All images were re-saved as JPEG q85 (Thermo images capped at 650 px wide).
  No single statistic separates the classes (AUCs 0.47-0.54).
- 86 of 93 manipulated images are "painting of background"; 7 are other within-blot types.

Images are not committed. `labels.json` has catalog numbers, Richardson summaries and source URLs.

## Results (12 batches of 15-16, blind sub-agents, Read tool only, 4 views)

| condition | F1 | precision | recall | TP | FP | FN | TN | AUC | F1 95% CI (by catalog) | painting | other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| no rules | 0.39 | 0.71 | 0.27 | 25 | 10 | 68 | 83 | 0.64 | 0.28-0.50 | 23/86 | 2/7 |
| rulebook v3 | 0.44 | 0.72 | 0.31 | 29 | 11 | 64 | 82 | 0.69 | 0.33-0.54 | 26/86 | 3/7 |

v3 vs no rules: fixed 16, broke 13, exact McNemar p = 0.71. No significant difference.

## Reading
- On real vendor blots, recall is low: about 3 in 10 painted backgrounds are found. Richardson
  spots most painting by raising contrast across many images from one vendor and seeing a patch differ
  from that vendor's usual background; one image at a time, many painted patches look like the
  over-processed flat backgrounds that clean images also have.
- Precision is about 0.7: 10-11 of 93 user-verified clean blots are flagged.
  - No rules: mostly "painting" or "splice" on Origene images.
  - v3: five false positives are type "other" (FLAG 8, "box around a band") on Origene images. The
    boxes are JPEG 8x8 blocks around bands on flat backgrounds (see the MA5-38397 discussion), so
    FLAG 8 fires on compression.
- Run-to-run noise in earlier tests was about 25% of verdicts, so the 4-image recall gain from v3 is
  within noise.

`runs/<condition>/V_<batch>.json` hold the raw verdicts; `prompt_rules_v3_example.txt` is the v3 prompt
for one batch (the no-rules prompt is the same without the rule block).

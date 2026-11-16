# Painted-background search in crawled Thermo blots: first pass (not working yet)

## Data
- **Positives:** 1,186 of Richardson's 1,473 Thermo "painting" images, taken from our own crawl so both
  classes went through the same download pipeline.
- **Negatives:** 58,576 crawled Thermo western blot images from products absent from his spreadsheets
  ("not flagged", not verified clean).
- **Confound:** 669 of the positives come from one upload (stamp 2017-12-19, MA5-2xxxx single-lane OEM
  layout). Evaluation is therefore done within each upload stamp.

## Findings
1. **Overall flatness** (feat_v1.py; noise-based flat share of the blot):
   - Within the 2017-12-19 upload: AUC 0.86. His flagged blots there are nearly fully flat lanes with a
     few textured remnants.
   - Other uploads: AUC 0.53–0.69.
   - Across uploads, flatness mostly encodes the upload's processing style.
2. **Vendor membrane texture is only 0–3 grey levels peak to peak.** Thermo's JPEG compression turns much
   of it into constant 8×8 blocks, so most "clean" blots already contain exactly constant areas inside
   their lanes.
3. **Lane-restricted, enclosed, exactly-constant patch** (feat_v2.py; 11×11 window, blot rectangle,
   textured lane columns, away from bands):
   - Synthetic uniform-grey patches painted into 286 textured unflagged blots (soft edge, JPEG q85):
     detection is no better than false alarms (0.21 vs 0.21 at 1,500 px).
   - Against Richardson's labels within uploads: AUC 0.17–0.71.
   - In 2017-12-19 it is reversed (0.17). His flagged blots there are flattened almost completely (no
     texture is left around the flat area), while 34% of unflagged ones have scattered constant
     JPEG blocks that join into large components.
4. **Some unflagged blots do show a large, coherent constant region surrounded by normal texture.**
   Examples: the upper lane at 100–170 kDa, or the region below 25 kDa. These look like real painting
   and are candidates for review, but the single-image score cannot separate them from compression.

## Next options
- **Per-layout baseline (Richardson's method):** within an upload family that shares a frame and
  processing, align blots on the frame. Flag regions that are constant in one blot but textured in most
  of its family.
- **Human calibration:** rank by the largest coherent constant region and label about 60 hits by eye, to
  measure precision directly.

## Human calibration set (select60.py) and the review view
- **Set:** 60 blots, shuffled and unlabelled. 40 are the top-ranked unflagged blots by largest enclosed
  constant patch (max 6 per upload stamp, 1 per product), 10 are Richardson-painted (positive controls)
  and 10 are zero-score blots (negative controls).
- **Review view:** `views.levels_richardson`.
  - Fitted on 339 of Richardson's original / "_levels" pairs: his adjustment is a linear stretch of a
    30-grey-level window (gain 8.5, gamma 1) centred on the membrane background, residual 0.3 grey levels.
  - Our version centres the window on each blot panel's most common textured grey level and changes only
    pixels inside the blot panels (`views.blot_mask_v2`, which also handles light-grey pages and trims
    ladder labels).
  - Agreement with his adjusted images inside the blot: median difference 2.2 of 255 grey levels, and
    within 20 on 96% of pairs.
- The first version of the page used whole-image histogram equalization. It over-amplified grain and
  recoloured the page around the labels, so it was replaced.

## Calibration result (user labels, 2026-11-16; review_results.json)
| Group | Painted | Not painted | Unsure |
|---|---|---|---|
| Top 40 detector hits (unflagged by Richardson) | 7 | 22 | 11 |
| 10 Richardson-painted (hidden positive controls) | 5 | 4 | 1 |
| 10 zero-score blots (hidden negative controls) | 0 | 9 | 1 |

- **Detector precision at the top of the ranking:** 7/40 (18%), or 7/29 (24%) of decided calls, against
  0/10 for zero-score blots. The difference is not statistically significant at this size (Fisher p ≈ 0.3).
- **By upload:** in the 2017-12-19 upload, 4 of the 6 top hits were called painted. In all other uploads,
  3 of 34.
- **Reviewer vs Richardson:** the reviewer called 5 of 10 Richardson-painted blots painted, so about half
  of his painting calls are not visible in a single adjusted image.
- **New painted candidates (not in Richardson's spreadsheets):**
  - 2017-12-19 upload: PDIA4 MA5-25771, MYF5 MA5-26654, HSPBP1 MA5-25667, RSPO1 MA5-26680.
  - SH3YL1 PA5-56593 (2021-05-27).
  - PYCARD PA5-85811 (2022-06-20).
  - TNK1 MA5-15413 (unstamped).

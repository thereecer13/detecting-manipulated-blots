# Band duplication within a blot: detector validation

## Method (`bandlib.search_copies`)
- **Find bands:** soft-edged dark blobs inside the membrane (`views.blot_mask_v2`), away from the panel
  border. Text, ladder ticks, chart bars and frame fragments are excluded by shape and edge sharpness.
- **Search for a copy:** for each band, look for it elsewhere in the same image in four orientations (as is,
  mirrored left-right, mirrored up-down, rotated 180°). Matches in the band's own column are skipped
  (marker ladders, parts of one smear).
- **Score:** the RMS pixel difference after alignment and a gain/offset fit, divided by the band's contrast
  range. A copy differs only by compression noise.

## Lessons from earlier versions
- Correlating the fine detail of two bands does not work: 18% of ordinary blots scored 0.98 or higher,
  because the edge shape of any two sharp bands correlates.
- A loose band finder matches chart bars, ladder ticks and labels.

## Validation
Known cases are Richardson's seven "bands are identical" Thermo blots, at 650 px width (crawl copies where
we have them).

| Case | Best difference | Orientation |
|---|---|---|
| MA1-12549 | 0.036 | same |
| MA5-12557 | 0.042 | rotated 180° |
| MA1-12648 | 0.055 | rotated 180° |
| MA5-16387 | 0.071 | same |
| PA5-27215 | 0.075 | same |
| PA5-17909 | 0.19 (missed) | |
| PA5-85730 | no bands found (missed) | |

Null: 3,000 random crawled Thermo blots not in Richardson's lists; 1,765 have at least one band.

| Threshold | Known cases caught | Unflagged blots at or below it |
|---|---|---|
| 0.040 | 1 of 7 | 16 (0.9%) |
| 0.055 | 3 of 7 | 46 (2.6%) |
| 0.075 | 5 of 7 | 174 (9.9%) |

The top-ranked unflagged blots include real-looking duplicates, so the null is not clean. Not yet reviewed
by a person:
- E2F4 PA5-79181, IGFBP-1 PA5-79448 and Caspase-8 PA5-95047: two-lane blots whose two bands are mirror
  images (differences 0.013–0.022).
- GPI MA5-25097 (A549 = COS7) and TACC3 MA5-25124 (HepG2 = A549).
- Phospho-GSK3B PA5-105582 (lanes 2 and 3).
- Histone H3 MA5-41199 (lanes 2 and 3, mirrored).

False hits among the top 10: small fragments on the edge of one large band (PA5-50832, MA5-38403, MA5-50638).

Not covered yet: the same band pasted into different blots (Richardson's pattern A groups).

## Full run (74,564 crawled blot images)

`run_search.py` over every crawled Thermo blot: 44,036 images had at least one band, 24,432 had a band with
a match elsewhere in the image. Best-match nrmse: <= 0.02 in 57 images, <= 0.03 in 259, <= 0.04 in 832.

`select60.py` builds the labelling set (`render.py` draws each item):
- filters: band at least 30 x 10 px; band and match must not overlap; chart bars rejected (one flat
  mid-grey fills more than 30% of the band box);
- one item per image, per catalog number; at most 5 per upload stamp, so that one upload cannot fill the set;
- 49 top candidates (nrmse <= 0.030), 5 of Richardson's within-blot cases, 6 low-score controls
  (nrmse 0.10 to 0.16), shuffled. Labels are pending.

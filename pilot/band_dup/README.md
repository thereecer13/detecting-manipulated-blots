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

## Round 1 labels (60 items) and the reviewer's criteria

| Set | duplicated | unsure | not duplicated |
|---|---|---|---|
| 49 top candidates | 7 | 4 | 38 |
| 5 Richardson within-blot cases | 3 | 0 | 2 |
| 6 low-score controls | 0 | 0 | 6 |

New candidates labelled duplicated: CABP5 PA5-86758, HDAC2 MA5-18061, PAX8 PA5-21368 and PA5-18457,
alpha-synuclein PA5-17239, GBA PA5-22326, TFAP2A PA5-17359 (GAPDH row). All seven are same-orientation
matches. The two Richardson cases labelled not duplicated (HA601015, BDNF PA5-85730) are the ones where the
search probably boxed a different pair from the one he flagged.

Reviewer's criteria (2026-11-17), which the pixel score did not capture:
- only whole-band duplications count, not parts of bands;
- heavily overexposed bands (uniform ovals) look alike without being copies;
- outline similarity is the main metric, fill similarity secondary;
- the more unusual the outline, the more convincing a close match;
- the same blot shown twice in one figure is not duplication (read labels, consider the figure's context).

`outline.py` turns these into features: outline IoU at 30/50/70% of band depth, whether the band or its
match touches the crop border (partial band), unusualness (1 - IoU with its own mirror images), saturation.
On the 60 labels, requiring a whole band, unusualness >= 0.05 and outline IoU >= 0.94 keeps all 10
duplicated items and removes 30 of the 46 not-duplicated ones. Outline IoU alone does not separate the
classes in this set (all candidates were already above 0.92).

`round2.py` applies that filter to every match with nrmse <= 0.05: 95 images pass (19 already labelled).
`build_page.py` builds the round-2 page from the 60 best-ranked unlabelled ones.

## Round 3: newly crawled blots, band groups and the cross-blot search

Why: a reviewer question on GBA PA5-22326 showed two gaps. The blot has three copies of one band (NIH:OVCAR-3
60 kDa, Hep G2 42 kDa, Hep G2 60 kDa; the third is about 7% wider) and a second pair (HeLa and HEK-293 at
60 kDa). `search_copies` keeps only the best match per band and compares at one scale, so it reported one pair.

Within one blot, new images: `run_search.py` over the 14,566 blot images crawled since the full run (8,508
with a band, 4,651 with a match). With the round-2 outline filter, 114 images pass in all (19 from the new
crawl); 23 were not labelled or on a page before (`review_r3_key.json`, ids W00-W22).

Band-to-band search (`cross.py`), 89,129 blot images:
- `bands`: whole bands of at least 30 x 10 px with an unusual outline (unusualness >= 0.05), identical files
  merged: 96,086 bands in 33,940 images. Each band gets a 32 x 16 normalised descriptor.
- `pairs`: descriptor similarity >= 0.985 in any of four orientations, sizes within 0.8-1.25, six best per
  band; pairs are across images of different products, or within one image in different lanes: 127,404.
- `verify`: aligned pixel difference with a gain fit of 0.6-1.6 (copies across blots often have changed
  contrast), outline IoU, and the correlation of the surroundings with the band masked out (`ctx`).
- Validation on Richardson's "may use the same band" notes: all three pairs present at one scale in the
  crawl pass (difference 0.026-0.042, outline 0.94-0.95, surroundings 0.64-0.72). They fail the within-blot
  gain limit of 0.8-1.25, which is why the limit is wider here.

Cross-blot results (`xgroups.py`; strict tier: same scale, difference <= 0.03, outline >= 0.94, both images
named after their product):
- 1,005 pairs; 506 are two products for the same target (set aside), 499 are different targets.
- The 499 pairs form 137 groups of 457 products. 95 groups contain only products already in Richardson's
  spreadsheets (nearly all pattern A; he notes the shared band for 8 of them). 42 groups include a product
  that is not in his spreadsheets (95 such products); 34 groups are entirely unlisted.
- By eye, before human review, the unlisted groups fall into:
  - one band on single-lane blots of different targets at different molecular weights: PA5-86xxx (two groups
    of 7, uploaded 2019-02-28), MA5-43xxx / PA5-122310 (6, 2022-04-13), MA5-2513x and MA5-2516x (2017-12-19),
    PA5-119095 / 119358 / 122068, TMEM27 MA5-43558 / COX2 PA5-119060, and unlisted members of pattern A / B
    families (e.g. IRX2 / BHLHE41 / p16INK4a, Cyclin G1 / SURF1, JNK / MEK, SPDL1 / phospho-PAK3);
  - a whole blot or a control row shown for two targets: ErbB4 PA5-95075 / TRIF PA5-95078, MBD4 PA5-79639 /
    TRAM2 PA5-95107, CYP2A7 / GPR176, PFKM PA5-51687 / GART PA5-51688, EHMT2 PA5-34971 (shows the FOXO3A
    knockdown figure of PA5-27145), shared loading or tag controls (H2B, GAPDH, MLC2, DDDDK tag);
  - look-alikes that are probably not the same band (e.g. WDR1 / ASS1, ABCG5 / Villin, DCI / CDK7).
- Excluded from the page: one group matched on figure text (histone peptide-array figures) and six groups
  whose two products are one target under two names (CD206, annexin A7, CD3e, PRKD2, MAOB).
- `build_page3.py` builds the pages: 3a within one blot (23 items), 3b across blots (35 groups). Labels pending.

Not covered: bands under 30 x 10 px, symmetric ovals, resized copies across blots (the strict tier is
same-scale only; 6,345 looser resized matches were not reviewed), and other vendors.

## Round 3 labels

Within one blot (`review_r3_within_results.json`, 23 items): 4 duplicated, 2 unsure, 17 not duplicated.
Duplicated: Phospho-CXCR4 PA5-105597, SNRPB PA5-27559, ATG3 PA5-17018, ABCA5 PA5-37131; unsure: HEXIM1
PA5-52629, Vinculin PA5-118351. None of the six is in Richardson's spreadsheets. All four duplicated items
are same-orientation matches; every mirrored or rotated candidate was labelled not duplicated.

Across blots (`review_r3_across_results.json`, 35 groups; this export used the first version of the page,
whose option "whole blot or control reused" did not say whether the reuse is acceptable):
- 20 groups "same band, different blots": 83 products, 51 of them not in Richardson's spreadsheets.
- 11 groups "whole blot or control reused". The reviewer's notes mark five as a problem: MBD4 PA5-79639 /
  TRAM2 PA5-95107 and ErbB4 PA5-95075 / TRIF PA5-95078 ("completely duplicated blot for different
  proteins"), PFKM / GART, Cyclin G1 / SURF1, JNK / MEK. The other six carry no note (influenza HA tag
  control, GNAI tag control, phospho-ERK / phospho-JNK, H2B loading control, MLC2 loading control,
  FOXO3A / EHMT2). Two groups labelled "same band" also carry reuse notes: CYP2A7 / GPR176 ("completely
  duplicated blot") and ABCF1 / PPFIA1 ("control is reused which is problematic").
- 4 groups "not the same band": WDR1 / ASS1, ABCG5 / Villin, PIK3R2 / SCLY, DCI / CDK7.

Display bug found by the reviewer: `build_page3.py` drew the group GIF without turning the second band when
the match was mirrored or rotated. Three groups were affected (G18, G20, G24); G20 and G24 were labelled
"not the same band" from misaligned GIFs. `pair_page.py` redraws a pair of blots with every matching band
pair boxed and each GIF turned and aligned (round 3c, `review_r3c_key.json`, labels pending):
- CDK9 PA5-86747 / TRF1 PA5-86084: two band pairs, both rotated 180 degrees and in reversed lane order.
  The whole three-band row of one blot matches the other blot's row rotated 180 degrees (NCC 0.97).
- FXYD2 PA5-75640 / Gng12 PA5-75620 and PANK2 PA5-75678 / PIK3CD PA5-86800: two shared bands each.
- ABCG5 / Villin and PIK3R2 / SCLY: many-to-many matches in every orientation (8 and 11 pairs between
  plain, near-identical ovals), which is what generic bands produce rather than a specific copy.

Round 3c labels (`review_r3c_results.json`): CDK9 / TRF1, FXYD2 / Gng12 and PANK2 / PIK3CD confirmed as
the same band in different blots; ABCG5 / Villin and PIK3R2 / SCLY confirmed as not the same band, now
from correctly aligned GIFs.

The six "whole blot or control reused" groups without a reviewer note, classified by the reviewer's rule
(acceptable only if the two products show the same protein, or share a control from the same experiment).
Judged from the figures and captions; whether a shared control came from the same membrane cannot be told
from the images.
| Group | What is shared | Call |
|---|---|---|
| Influenza HA MA5-56606, MA5-56607 (H9N2), MA5-56759 (H3N2) | DDDDK-tag row; same panel of tagged HA transfectants in the same lane order, same upload | acceptable: shared control, same experiment |
| GNAI1/2/3 MA5-50379, GNAI3 MA5-50380 | DDDDK-tag row; same 293T transfectant panel, same upload | acceptable: shared control, same experiment |
| Phospho-ERK MA5-15174, phospho-JNK MA5-15175 | one three-panel figure (phospho-p44/42, phospho-p38, phospho-JNK) shown on both products, each panel labelled with its own target | acceptable: same protein in the matched panel |
| H2BK20ac MA5-24698, H2BK12ac PA5-40100 | total histone H2B row; same HeLa / COS-7 butyrate lysates; the acetyl-H2B blots differ; uploads six days apart | acceptable: shared control, same lysate set |
| Phospho-MYL2 Tyr118 PA5-67499, Ser15 PA5-67500 | total MLC2 row; same U87 interphase / cytokinesis lysates, same upload; the phospho blots differ | acceptable: shared control, same experiment |
| FOXO3A PA5-27145, EHMT2 PA5-34971 | the whole figure. The EHMT2 product's "knockdown" image is the FOXO3A figure (labelled C2C12, FOXO3A shRNA, FOXO3A), while its caption describes EHMT2/G9a shRNA in 293T cells | not acceptable: the figure shows a different protein from the product |

Totals for the cross-blot round after all labels: 20 groups with one band on different blots, 8 groups with
a blot or control reused in a way that is a problem (MBD4 / TRAM2, ErbB4 / TRIF, PFKM / GART, Cyclin G1 /
SURF1, JNK / MEK, CYP2A7 / GPR176 and ABCF1 / PPFIA1 by the reviewer's notes; FOXO3A / EHMT2 by the rule
above; the last two reviewer-noted groups are also counted among the 20), 5 acceptable reuses, 4 not the
same band.

## Round 2 labels and what separates the classes

Round 2 (`review_r2_results.json`, 60 items): 10 duplicated, 2 unsure, 48 not duplicated. Duplicated: TCF7L2
PA5-78192, ATP5J PA5-29202, IFT88 PA5-18467, IFI16 PA5-76462, RPS19 PA5-75564, GBA MA5-26589 (the product
is in Richardson's spreadsheets), DNMT3L PA5-76619, ATF4 PA5-27576, SMAD2/SMAD3 PA5-17621, and a published
figure listed under PA5-27822 (not a vendor blot). Unsure: HDAC8 PA5-79353, KRT7 MA5-15604.

With rounds 1 to 3 every within-blot candidate that passes the outline filter has been labelled: 129
decided items (excluding the low-score controls), 24 duplicated and 105 not.
- Fill match (1 - nrmse) does not separate them at all (AUC 0.50): duplicated median 0.968, not 0.971.
  Raising the pixel threshold would not help.
- Orientation does: 22 of 24 duplicated items are same-orientation matches, while 60 of 105 rejected items
  are mirrored, flipped or rotated matches.
- Unusualness of the outline is the best single feature (AUC 0.81; duplicated median 0.20, not 0.09);
  outline IoU is weaker (AUC 0.68).
- Rule for further screening: same orientation and (unusualness >= 0.15 or outline IoU >= 0.96). It keeps
  22 of 24 duplicated items and 18 of 105 rejected ones (precision 0.55, against 0.19 for the filter used
  so far). The two it loses are the rotated and flipped matches.

## Border similarity (`border.py`)

Reviewer's point: the filled interior of a dark band matches any other dark band, so similarity should be
measured on the band's border. Edge zone = within 2 px of the half-depth outline of either band. On the 129
decided within-blot items (24 duplicated, 105 not):

| Feature | Duplicated (median) | Not (median) | AUC |
|---|---|---|---|
| whole-patch pixel similarity (the "fill match" shown so far) | 0.968 | 0.971 | 0.50 |
| pixel similarity in the edge zone (RMS difference) | 0.958 | 0.956 | 0.50 |
| correlation of the pixels in the edge zone | 0.987 | 0.969 | 0.78 |
| correlation of the fine detail in the edge zone (image minus a 1.5 px blur) | 0.953 | 0.725 | 0.84 |
| outline unusualness | 0.195 | 0.091 | 0.81 |
| pixel similarity of the interior only | 0.988 | 0.975 | 0.84 |

- An RMS difference is the wrong measure anywhere: it is dominated by the steep edge gradient, where a
  sub-pixel shift costs as much as a different shape. The correlation of fine detail along the border is
  what separates copies from look-alikes.
- The interior is not uninformative once the border is excluded, probably because many bands are not
  saturated and carry their own texture.
- Sum of standardised border detail and unusualness, plus one point for a same-orientation match: AUC 0.92;
  the 40 best-ranked of the 129 items contain 22 of the 24 duplicated. This is fitted and tested on the same
  labels, so the next labelled set is the real test.

## Border score applied to the cross-blot matches (`cross_score.py`)

Score = standardised border detail + standardised unusualness (smaller of the two bands) + 1 for a
same-orientation match, with the means and standard deviations of the 129 labelled within-blot items.
Cutoff 1.46 = the score of the 40th of those 129 items.

Check against the round-3 cross-blot labels: all four groups labelled "not the same band" score below the
cutoff (best pair 0.74 at most). Of the 20 groups labelled "same band", 14 have a pair above it; six do not
(e.g. the MA5-2516x group, the CDK9 / TRF1 rotated row), so the cutoff loses real cases.

All 8,671 verified cross-blot pairs (difference <= 0.05, outline >= 0.92, including resized matches) were
scored. 7,372 are between product-named images of different targets; 7,177 of those are outside the groups
already reviewed, and 1,174 score above the cutoff: 749 between two products already in Richardson's
spreadsheets, 425 involving a product that is not. The 1,174 pairs form 315 groups; 242 include an unlisted
product (552 unlisted products), 73 are listed-only.

Of the 242 groups, 55 have a same-size pair above the cutoff and 187 match only after resizing. By eye the
same-size matches at the top are mostly convincing, while resized matches are mostly look-alikes with a few
real ones; the score was fitted on same-size pairs and is less reliable after resizing. Round 4 page
(`review_r4_key.json`, labels pending): the 28 best same-size groups and the 12 best resized-only groups,
one pair of blots per group, drawn with `pair_page.py` (every matching band pair boxed, second band turned
and aligned in the GIFs).

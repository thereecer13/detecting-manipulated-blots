# Cross-image reuse that Richardson's spreadsheet does not record (first pass)

Richardson's spreadsheet lists only flagged images: 13.8k of 18.9k rows are shared template
backgrounds (patterns A-H), the rest are single-image problems (mostly "painting"). This pass looks
for reuse between images that he lists only for single-image problems, and between those and the
scraped vendor blots that are not in his list.

Method: `../find_shared_backgrounds.py` (panel noise fingerprints, compared within aspect-ratio bins),
then `classify_pairs.py` (same picture vs different content) and checks at native resolution.
Searched: 5,000 Richardson images without a cross-image note, 112 scraped images, 40 exemplars per template.

## Lessons from building the search (each one produced false matches first)
1. Printed ladders and labels have the same layout across a vendor's figures; whole-image noise
   correlates ~1. Mask the white page and a margin around it.
2. Edge ringing and lane streaks are 1-D and shared by layout: remove residual row and column means.
3. Upscaling small images (Origene 102-px lanes) to a fixed width turns the shared JPEG 8x8 grid into
   fake shared texture. Verify every candidate at native resolution.
4. Origene two-panel figures (product antibody + anti-DDK control) correlate at 0.3-0.5 even between
   unrelated figures after removing the JPEG grid and row/column structure. A background match on
   Origene needs a control from unrelated figures before it counts as evidence.
5. A matching band shape is not evidence: a generic oval band on a flat lane matches unrelated lanes
   at 0.85-0.94 by template matching.

Validation on Richardson's templates: copies of one template score median 0.58 (5th percentile 0.16),
different templates never above 0.17; many template images are too flat to fingerprint.

## Confirmed by eye: same blot shown for different products, not linked in the spreadsheet
| vendor | catalogs | products | what is shared | Richardson's note on each |
|---|---|---|---|---|
| Abnova | RAB01425 / RAB01426 | IQGAP2 / IHH (different proteins) | identical image; band at ~45 kDa (IQGAP2 is ~180 kDa) | repetitive background noise |
| Abnova | RAB01473 / RAB01474 | CDK9 / CDC37 (different proteins) | identical image | repetitive background noise |
| Origene | TA504776 / TA504777 / TA504830 | NONO, clones OTI3F8 / OTI4D9 / OTI2C9 | same KO-validation figure, caption changed; panel A noise corr 0.95 | painting |
| Origene | TA502635 / TA502593 | ARFGAP1, clones OTI2C10 / OTI1F6 | same figure; panel A noise corr 0.96 | painting |
| Origene | TA501635 / TA501632 | NSE2, clones OTI6A6 / OTI4A2 | same figure; panel A noise corr 0.99 | painting |

## Open (needs a biologist's eye and unrelated-figure controls)
- Origene SERPINB6 TA504355 / TA504127 and ALDH1A3 TA502805 / TA502841: panel A bands differ but the
  background matches (0.89, 0.82). Copied background under different bands, a stripped and
  re-probed membrane, or the shared Origene background structure (lesson 4).
- Scraped TA815678 / TA815680 (marked clean in review): whole-image native correlation 0.61.
- ~50 Thermo Fisher MA5- / Bioss bsm- pairs (and Thermo / HUABIO, Origene / Boster) share identical
  images under different clone names. Probably one manufacturer supplying both (OEM), not image reuse
  within a vendor.

`reused_images_candidates.json` lists all near-identical pairs across catalog numbers (score, catalogs,
titles, Richardson's notes). The `category` field is a rough title parse and is wrong where the
gene symbol sits in parentheses; the tables above were checked by hand.

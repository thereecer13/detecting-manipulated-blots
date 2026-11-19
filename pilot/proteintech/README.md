# Proteintech IHC images: copy-move and spot cleaning

Images: 739 IHC images from 600 Proteintech antibody product pages (sitemap sample, `pilot/scrape_ptg.py`).

## Large copy-move (`pilot/copy_move.py`)
SIFT self-matching with affine / mirrored models and pixel verification. Synthetic test: 150/200 pasted
regions found, 0/200 false alarms. Real images: 0 hits.

## Small cloned spots (`pilot/spot_clone.py`, v2)
Synthetic soft-brush clone-stamp spots (14-34 px): 28/57 found at area >= 60 px, 2/30 clean images with
an alarm. On the 739 real images 192 were flagged (real IHC has much more repetitive texture than the
synthetic negatives). The top 48 were checked with difference maps (the region against the region at
the detected offset; a copied area shows as a compact block that is identical while its surroundings
differ):

| Product | Image | Offset | Call |
|---|---|---|---|
| 16611-1-AP (MRPL46) | MRPL46-Antibody-16611-1-AP-IHC6192.jpg | 55 px right | **likely copy**: a hard-edged ~50 x 30 px block identical to the area beside it, inside tissue that differs everywhere else |
| 22980-1-AP (PRODH) | PRODH-Antibody-22980-1-AP-IHC-4967.jpg | (9, -78) | possible: compact soft-edged identical patch in fine-grained texture (the product's other image IHC-4968 also flagged, less clearly) |
| 51105-1-AP (ERBB2) | ERBB2-Antibody-51105-1-AP-IHC22545.jpg | (37, 16) | possible: compact soft-edged identical patch; image has strong colour fringing |
| the other 45 checked | | | false: flat background, lumens, periodic tissue (muscle striations), edges |

These need a human look at the original files before anything is said publicly. Images ranked below
48 (area < 91) were not reviewed.

### Update: every duplication per image, exact outlines
The detector now keeps every matching region (>= 30 px) at every candidate offset, drops repeats, and
saves each region's outline; regions with the same offset are fragments of one copied patch and are
drawn as one numbered duplication. Rescan of the 192 flagged images (`spot_v3`). Duplications whose
fragments total >= 120 px, checked with difference maps:

| Product / image | Duplications | Call |
|---|---|---|
| MRPL46 16611-1-AP, IHC6192 | 2: offset (55, 0), 593 px; offset (45, 33), 696 px | **likely copied, twice**: both are compact areas identical to the area at the offset, inside tissue that differs everywhere else |
| PRODH 22980-1-AP, IHC-4967 | 3 compact patches (offsets (9,-78), (26,35), (11,59)) + 1 false (fibre edge on flat background) | possible: offsets run along the muscle fibres, whose texture repeats along the fibre axis |
| PRODH 22980-1-AP, IHC-4968 | 4 (447, 365, 275, 169 px) | weaker: scattered, blotchy agreement in granular muscle texture |
| ERBB2 51105-1-AP, IHC22545 | 2 (233, 122 px) | possible (image has strong colour fringing) |

Most flagged images also carry many small (60-95 px) look-alike regions; the count of regions per image
is not by itself evidence.

### User review (18 Nov) and the remaining flagged images
The four images above (MRPL46 IHC6192, PRODH IHC-4967 and IHC-4968, ERBB2 IHC22545) were all labelled
"copied" by the reviewer.

Remaining 188 flagged images: every (image, offset) group of >= 60 px was scored by the mean pixel
difference inside the matched outline against a ring around it (a true copy is identical inside and
different outside; the confirmed groups have inside ~5-17, ring ~30-90). Groups with ring/inside >= 2
that are not on pale background (< 25% of pixels above 225, mean brightness < 215): 57 groups in 35
images, all checked by eye with difference maps. Most are the web of pale background between nuclei,
which matches itself at many offsets. Sent for review (`build_review.py`, key `review2_key.json`):

| Product / image | Candidates | My call |
|---|---|---|
| 20097-1-AP, IHC20084 | offsets (31, 2) 251 px and (17, 3) 61 px | likely: compact identical patch in textured stained tissue |
| 14648-1-AP, IHC11982 | (42, 9) 60 px | possible |
| 66483-1-Ig, IHC-169089 | 4 offsets, 67-82 px | possible: compact patches among cells |
| 26980-1-AP, IHC-97820 | 2 offsets, 81-87 px | possible |
| 16661-1-AP, IHC9483 | (33, -12) 83 px | weak |

### Round-2 labels (18 Nov)
Reviewer: only 20097-1-AP IHC20084 is copied; the other four (14648-1-AP, 66483-1-Ig, 26980-1-AP,
16661-1-AP) are not. Rule from the reviewer: call a duplicate only when the match is exact and
continuous, not patchy. Confirmed so far: 5 images of 739 (MRPL46 16611-1-AP, PRODH 22980-1-AP x2,
ERBB2 51105-1-AP, 20097-1-AP).

Continuity measure tried: pixels identical at the offset (max channel difference <= 14) and textured,
opened with an 11x11 square; area of the largest remaining block. Confirmed groups: 121-337 px for
PRODH, MRPL46 (55, 0) and 20097-1-AP (31, 2); every rejected group 0. It misses ERBB2 (0; colour
fringing) and MRPL46 (45, 33). Unlabelled groups with a large block and a clearly different ring are
still to be checked by eye (29190-1-AP, 16034-1-AP, 25616-1-AP among them).

### Round-3 labels (18 Nov)
The nine images surfaced by the continuity measure alone (`review3_key.json`): none copied (reviewer).
They were pale background or striated muscle. Reviewer's further point: spots this small are not worth
calling; a person cleaning an image would not bother with blemishes that size. Rule going forward: a
solid block of exactly matching pixels, textured and stained inside, different surroundings, and a
minimum size set from the confirmed copies (matched area >= ~200 px).

### Fast solid-block scan (`block_clone.py`, 18 Nov)
Built on the reviewer's rules (exact, continuous, stained, surroundings differ, not tiny). About 3.5 s
per image (the spot scan took ~2 min). On the first 737 images: 21 images flagged, 61 blocks.
- Confirmed images found again: MRPL46 IHC6192, PRODH IHC-4967 and IHC-4968, ERBB2 IHC22545 (4 of 5;
  20097-1-AP IHC20084 is missed). New larger areas in two of them: PRODH IHC-4967 offset (19, 64),
  594 px; ERBB2 offset (67, -13), two blocks of 261 and 224 px.
- New: 17363-1-AP IHC9569, offset (6, 120), two adjoining blocks of 805 and 594 px (likely);
  22462-1-AP IHC-90506, offset (21, -3), 154 px (possible).
- False by eye: three images with 7-17 blocks each at short offsets in striated or smooth tissue
  (84854-5-RR, 84281-5-PBS, 85857-4-RR) and ten single blocks on pale or blurred areas.
Sent for review as round 4 (`review4_key.json`). Minimum offset raised from 12 to 16 px afterwards.

### Round-4 labels (18 Nov, `review4_results.json`)
Copied: 17363-1-AP SLC30A3 IHC9569 (new image), and the new areas in PRODH IHC-4967 and ERBB2 IHC22545.
Not copied: 22462-1-AP GNRHR IHC-90506 (154 px, the smallest block shown).
Confirmed images so far: 6 of 737 (MRPL46 16611-1-AP, PRODH 22980-1-AP x2, ERBB2 51105-1-AP,
20097-1-AP, SLC30A3 17363-1-AP). On the fast scan's blocks, every one labelled copied is >= 221 px and
the one labelled not copied is 154 px.

### Larger crawl (19 Nov)
`scrape_ptg.py --n 3600 --seed 1` finished: 3,600 sampled product pages, 4,587 IHC image records
(the first 600 pages / 739 images are the set above). `block_clone.py scan --skip 739` on the rest:
3,812 images scanned, 92 flagged, 17 images with a block >= 200 px among those with at most four blocks.
- Sent for review as round 5 (`review5_key.json`), five images: 21310-1-AP NHLRC1 IHC25136 (757 px),
  12166-1-AP IHC19537 (407 px), 14055-1-AP IHC14081 (379 px), 11600-1-AP IHC2313 (268 px),
  16518-1-AP IHC4835 (200 px). Labels pending.
- Rejected by eye as blurred, pale or striped background (no clean block in the difference tile):
  21990-1-AP, 21214-1-AP, 67299-1-PBS, 60054-1-PBS, 17535-1-AP, 66868-1-PBS, 21771-1-AP, 24378-1-AP,
  67539-1-Ig, 23153-1-AP, 85933-1-RR (1,298 px on faint horizontal scan lines in empty background).
- Images with more than four blocks (e.g. 14221-1-AP with 58) were not tiled; in the first set those
  were all repeating tissue texture.

### Round-5 labels (19 Nov, `review5_results.json`)
Copied: 16518-1-AP RNASEH2C IHC4835 (200 px), 21310-1-AP NHLRC1 IHC25136 (757 px), 12166-1-AP FXYD5
IHC19537 (407 px), 14055-1-AP USP16 IHC14081 (379 px). Unsure: 11600-1-AP HCK IHC2313 (268 px).
Confirmed images in total: 10 of about 4,550 scanned (6 in the first 737, 4 in the next 3,812).
The 200 px block is the smallest labelled copied so far; 154 px remains the only "not copied" block.

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

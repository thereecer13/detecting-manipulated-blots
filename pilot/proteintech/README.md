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

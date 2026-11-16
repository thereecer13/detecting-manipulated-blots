# Aligned overlay GIFs: new pattern A and pattern B members vs Richardson's examples

Output (outside the repo): reviews/thermo_controls/patternB_overlay.gif and patternA_overlay.gif.

Each blot is registered to Richardson's example on lane texture alone:
- the texture is high-pass filtered, with row and column structure removed;
- bands and the frame are masked out;
- pattern B is fitted by resize plus a sub-pixel shift (same layout, same aspect);
- pattern A is fitted by a masked template-match scale search, because the 2021 crops differ.

The control is the same score with the candidate flipped vertically.

| Pattern | Reference (Richardson) | New blot | Texture r | Flipped control |
|---|---|---|---|---|
| B | PA5-101612 GRB14 | PA5-99397 IL-5 | 0.59 | -0.02 |
| B | | PA5-99460 Gastrin | 0.53 | -0.01 |
| B | | PA5-99462 CDKN2C | 0.50 | -0.02 |
| B | | PA5-116113 VEGFB | 0.52 | -0.01 |
| B | | PA5-99455 PIASy | 0.76 | 0.00 |
| B | | PA5-99429 NOTCH2 | 0.56 | -0.01 |
| B | | PA5-99468 Cyclin C | 0.54 | -0.01 |
| B | | PA5-99414 HOXB5 | 0.50 | -0.01 |
| B | | PA5-99210 TBX10 | 0.49 | -0.01 |
| B | | PA5-118870 PTPN22 | 0.72 | -0.01 |
| B | | PA5-118826 ACVRL1 | 0.61 | 0.00 |
| A | PA5-102052 EDG4 | PA5-116143 ZDHHC7 | 0.51 | -0.09 |
| A | | PA5-118794 CaV1.3 | 0.40 | -0.08 |
| A | | PA5-118800 NKCC1 | 0.46 | -0.07 |
| A | | PA5-118886 EVL | 0.60 | -0.04 |
| A | | PA5-118893 ELF5 | 0.56 | -0.09 |
| A | | PA5-118900 SRRM2 | 0.41 | -0.04 |
| A | | PA5-118907 CABP5 | 0.57 | -0.04 |
| A | | PA5-118918 USP24 | 0.61 | -0.08 |

Pattern A scale for the 650×650 crops is 0.749–0.752 with offset (-87, 0), the same for every blot.

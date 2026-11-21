# PMC13481467, Fig 5E: blog figure for the rotated transwell image

Inflamm Res 2026, doi:10.1007/s00011-026-02342-2 (CC BY 4.0). Confirmed by the user (cell round 4).
Chosen for the blog post as the best-resolution case of a copy turned by an odd angle: the article PDF
in the PMC open-data bucket carries Figure 5 at 2056 x 2759 px (the web JPEG is 685 x 919), so each
transwell panel is 390 x 312 px.

`rotated_panels.py` registers the "NC+LPS" panel onto the "OE-Vector+LPS" panel and draws the figure
(`PMC13481467_Fig5E_rotated_reuse.png`, kept with the review files, not in the repo).
`measurements.json`: 233 of 256 matched points fit one rotation of 107.6 degrees at scale 1.002 with a
mean error of 0.83 px; the shared area is 73% of the panel; pixel correlation there is 0.84, against
0.01 and 0.03 for the figure's other two panels.

`simple_figure.py` draws the plain version the user asked for instead: the two published panels and the
first one turned to the matching angle, no outlines or numbers (`PMC13481467_Fig5E_rotated_simple.png`).

`two_panel_figure.py` is the version the user settled on: NC+LPS as published, and OE-Vector+LPS turned
108 degrees with a rectangle marking the NC+LPS frame (`PMC13481467_Fig5E_two_panel.png`).

`overlay_figure.py`: three panels, with the middle one a half-transparent overlay of NC+LPS and the turned
OE-Vector+LPS (`PMC13481467_Fig5E_overlay.png`).

Blog version: `overlay_figure.py ... --anon` labels the panels Sample A / Sample B, drops the source line and
writes `rotated_reuse_overlay_anonymized.png` (the user asked for the source removed and the names anonymised).

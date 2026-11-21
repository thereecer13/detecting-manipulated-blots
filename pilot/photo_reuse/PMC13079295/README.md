# PMC13079295, Fig 5: three wound photographs from one photograph

Front Bioeng Biotechnol 2026, doi:10.3389/fbioe.2026.1800416. The caption gives panels A, B and C
as "dorsal full-thickness skin wounds showing healing progression at day 3 (A), day 7 (B), and
day 14 (C) post-injury".

Found by the cell-culture scan as a match between A and B (the figure's caption matched "wound").
The user confirmed the A/B duplication and asked whether anything else was wrong with the three
images. `three_panels.py` registers B and C onto A and measures them; numbers in
`measurements.json`, figure and blink animation in the reviews folder
(`PMC13079295_Fig5_three_panels.png`, `PMC13079295_Fig5_blink.gif`).

What the three panels are:

- **One photograph.** B maps onto A with a plain 1.20x zoom and a shift (297 matched points,
  none lost when a general affine fit is allowed). C maps onto A only with a stretch: 127 matched
  points with x-scale 1.02 and y-scale 0.81, against 51 with a plain zoom. So C is the same
  photograph stretched about 25% vertically and cropped (the glove, ear and paw mostly fall
  outside the crop). The ruler, the grey object under its left end, the glove edge, the table
  speck and the animal's lower outline coincide in all three.
- **The wound is cut shorter in B and C.** In A's frame the wound's left end is at the same pixel
  in all three panels (x 79.1, 79.2, 78.0; y 111.6, 111.6, 111.7). Its right end is at x 146.8 in
  A, 124.5 in B and 96.6 in C. By the ruler in the photograph (21 px per cm) that is 3.3, 2.2 and
  0.9 cm: 100%, 67% and 27%.
- **The fur around the wound is smoothed in B and C.** Fine texture (high-pass standard deviation)
  on the back left of the wound falls to 0.35 of A's value in B and 0.34 in C, while the ruler face
  (1.03, 1.01), glove (1.05), wall (1.17) and table (1.06) keep theirs. The skin creases and pink
  marks visible in A are gone in B and C.

Other points, from the paper's own text:

- Methods: "the dorsal skin was shaved and disinfected with povidone-iodine solution. A
  full-thickness linear wound approximately 3 cm in length ... was created". The animal in the
  photograph is not shaved, and the wound in A measures about 3.3 cm, the full starting length,
  with fresh red blood. A looks like a photograph taken at wounding rather than at day 3 (my
  reading, not something the image can prove).
- Methods: photographs "obtained using a digital camera (EOS 80D ...) positioned at a fixed
  distance". The framing differs between the panels only by the zoom and stretch above.
- Panel D plots "wound closure (%)" for individual animals, defined as the percentage reduction in
  wound area from baseline. Two of the day-14 nanocellulose points lie above 100% (about 103 and
  111).

Limits: the published figure is small (each photograph 233 px wide in the PMC copy), so the
measurements are to about a pixel. The publisher's larger version would sharpen them.

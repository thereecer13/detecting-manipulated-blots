# PMC8201856, Fig 5b: which mouse panels are the same photograph

J Nanobiotechnology 2021, doi:10.1186/s12951-021-00932-2. Fig 5b is a 3 x 5 grid of bioluminescence
images: rows D0, D7, D14; columns PBS, aPD-L1, BPQDs+NIR, BBPQDs+NIR, BBPQDs+NIR+aPD-L1.

All 15 panels show four white mice in one holder on one stage, so different photographs already
look alike, and the keypoint matcher's boxes ran across panel borders. `panel_matrix.py` instead
compares every panel with every other (105 pairs): best shift within 14 px, score = correlation of
the greyscale photograph over the animals and tails, colour signal and holder bar left out.
Results in `panel_matrix.json`, picture `PMC8201856_Fig5b_panel_matrix.png`.

- 101 pairs score 0.72 or less (median 0.57).
- Four pairs score 0.86 to 0.89, and on viewing show the same poses, limbs and tail curves:
  D0 aPD-L1 = D14 aPD-L1; D0 BPQDs+NIR = D14 BPQDs+NIR; D7 BPQDs+NIR = D0 BBPQDs+NIR;
  D7 BBPQDs+NIR = D0 BBPQDs+NIR+aPD-L1.

Correction: the first review page (21 Nov) said three D7 panels matched D0 panels one column to
the right. The D7 aPD-L1 / D0 BPQDs+NIR pair scores 0.44 and is not a match; the keypoint box had
simply spanned three panels. The page was rebuilt with the four pairs above, each boxed as a whole
panel.

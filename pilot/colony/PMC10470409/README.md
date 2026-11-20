# PMC10470409 Fig 7B, the two shS+NPHP4 plates

Scripts used on the largest copy of the figure the user could obtain
(plates about 765 px across). The image itself is not in the repo.

- `big1.py` split and align by colony centres. Result: lower plate ->
  upper plate is a pure 1.112x zoom plus shift; rotation 0.02 degrees,
  x and y scale equal to 0.1%; residual 0.46 px median over 44 colonies.
- `big2.py` one-sided colonies in the shared area: 10 only in the upper
  plate, 12 only in the lower, of 57 and 58. Pixel agreement 0.84.
- `big3.py`, `big4.py` are the one-sided colonies copies of other
  colonies? No: best look-alike scores 0.74-0.97, inside the range of
  unrelated colonies (up to 0.97); a true copy scores about 0.98.
- `big5.py` are the empty spots smoothed or cloned? No: texture level is
  inside the normal background range at 20 of 22 spots (the other two sit
  on faint specks), and no background patch repeats elsewhere above chance.
- `big6.py` background detail between plates: correlation 0.81 at 4-12 px,
  0.45 at 1-3 px, 0.15 below 1.5 px; enhanced close-ups of all 22 spots.

Reading: same photograph at two zoom levels (the exact zoom with no
rotation makes two separate photographs of one plate unlikely), with about
22 colonies differing. No editing remnants found; fine grain is not
preserved in this file, so that does not clear it.

The two older scripts in this folder ran on smaller copies; the first
version of the comparison used a drifted alignment (see ../README.md).

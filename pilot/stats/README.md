# Statistics on the confirmed papers

`collect.py` gathers the papers confirmed by the user from the results files
(cell-assay and animal-imaging scans, colony plates, flow cytometry): 116
papers on 22 Nov 2026. Vendor images (blots, IHC) are not publications and
are left out.

Metadata comes from the Europe PMC search API (`PMCID:` queries, core
results): citation count, journal, year, author affiliations. Country is
the country of the first author's first affiliation that can be parsed
(`countries.py`). `baseline.json` (not committed) is the same metadata for
300 random papers from each of the two large scans, used to compare the
share of papers from China (cell-assay scan: 77% of scanned, 67% of
confirmed; animal-imaging scan: 44% and 45%).

`plots.py` draws the figures into `/home/user/reviews/stats/`.
`confirmed_papers.csv` is the table behind them.

Not done: journal impact factors. They are proprietary (Clarivate), the
OpenAlex equivalent needs an API key and Scimago blocks scripted downloads.
A journal metrics export joined on the `issn` column would fill this in.

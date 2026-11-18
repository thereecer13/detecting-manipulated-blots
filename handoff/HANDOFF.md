# Handoff: state of the work on 2026-11-18, 01:35 UTC

The cloud session that produced this work reported "out of disk, memory or time". This folder holds
everything needed to continue in a new session except the downloaded images (about 20 GB), which are
not in the repository and must be fetched again where needed.

## What is here
- `crawl_state.tar.gz`: progress and index files of the Thermo PA5/MA5 crawl (`pilot/crawl_icc.py`).
  `icc_all/done.txt` lists finished product pages (90,141 of 99,705 on 18 Nov, 07:36 UTC); `icc_all/index.jsonl` and
  `icc_all/media.jsonl` list every microscopy figure (URL, caption, file hash); `icc_all/wb/scraped.jsonl`
  lists every western blot image; the other files are the earlier scrapes passed to `--skip` / `--have-wb`.
- `band_state.tar.gz`: band-duplication results: within-blot search output for 89,129 blots
  (`band/m_items.json`, `band/m_out.json`), cross-blot bands, verified pairs and groups (`band/xall/`),
  and the keys of review rounds 1 to 3.
- `facs_state.tar.gz`: flow-plot panels and matches for the first 1,000 papers (`facs/pmc/`) and for
  chunks 1 to 5 of the 9,000-paper scale-up (`facs/pmcbig/cK/`), plus the control-panel batch selections.
- `scripts/`: helper scripts that lived only in the scratch directory (`batch.sh` runs one control-panel
  batch; `sp/list_new.py` lists new pairs; `shift2.py` checks pattern C blot hits; `facs/run_chunks.sh`
  runs the FACS scale-up; `band/` is a copy of the working band scripts).

## To resume in a new session
1. Unpack the three archives into one scratch directory, keeping paths.
2. Thermo crawl: run `pilot/crawl_icc.py --out icc_all --skip media_all.jsonl ctrl_sample/media.jsonl
   --delay 2 --have-wb scraped_tmpl/scraped.jsonl scraped_ma5/scraped.jsonl scraped_members/scraped.jsonl`.
   It skips pages in `done.txt` and continues with the remaining pages. Images of finished pages are
   not re-downloaded by this command; scanning new pages against old ones needs the old images, which
   can be re-fetched from the URLs in `media.jsonl`.
3. Control-panel batches 1 to 58 are reviewed (`pilot/controls/README.md`, 633 confirmed pairs).
   Batch 59 (crawl pages from ~88,600) was running and is not reviewed.
4. FACS scale-up: all 9 chunks are done and pre-screened (see pilot/facs/README.md); labels pending (threshold:
   coinciding dots minus chance >= 20). Re-fetching figures: `pilot/facs/fetch_pmc.py --start K000 --n 1000`.
5. Band duplication: rounds 1 to 3 are labelled; round 4 (cross-blot, border score) is pending (pilot/band_dup/review_r4_key.json);
   keys are `pilot/band_dup/review_r3_key.json` and, in the archive, `band/review_r2_key.json`.

## Constraints agreed with the user
- Vendor and journal images stay out of the repository.
- Polite scraping: obey robots.txt, honest user agent, 2 s delay for Thermo. PMC figures come from the PMC
  Open Access bulk service only (not Europe PMC).
- Read captions and context before calling anything a duplication.
- Work on branch `claude/clever-ritchie-m1namn`; no pull request unless asked.

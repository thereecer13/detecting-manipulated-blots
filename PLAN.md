# Plan: can Claude spot manipulated western blots, and can biology rules help?

Two questions, in order:

1. **Baseline.** Can Claude find manipulation in western blots out of the box, and how good
   is its F1? Two tasks:
   - **Task A (single blot):** one blot crop. Is it manipulated within itself (duplicated
     bands or background, a spliced lane, a painted background)?
   - **Task B (blot pair):** two blot crops that are supposed to come from different
     experiments. Do they share reused content (the same background or bands)?
2. **Expert rules.** If F1 is low, does a rulebook written from your biology knowledge
   raise it? Does the gain come from the biology itself, not from a longer prompt or a
   moved threshold?

**Scope:**
- Western blots only: no DNA/RNA gels, Coomassie/SDS-PAGE stains, IHC or other assays.
- Claude models only: Opus 5.5 (main), Sonnet 5.5 and Haiku 5.5.
- The unit of judgment is a single blot crop (task A) or a pair of single blot crops
  (task B).
- Task B is a **verification** task: Claude is handed a pair and judges that pair. Finding
  reuse across a whole collection would need every image compared with every other one,
  which is far too many calls. Section 3.4 shows the practical alternative: a cheap
  classical step proposes candidate pairs, and Claude checks only those.

This is a different task from the Level 1 work in `fake-blot-detection` (AI-generated vs
real). That repo's image normalization, Claude detector, metrics and shortcut check can be
reused here (see [Infrastructure](#8-infrastructure)).

---

## 1. The data

### BioFors (Sabir et al., ICCV 2021)

27,440 images are labeled `Blot/Gel`. They are already cropped to one panel each. Ground
truth comes as bounding boxes.

| task | BioFors annotation | blot/gel data |
|---|---|---|
| A | **IDD** (duplication within an image) and **CSTD** (cut or sharp transition) | **218 images** (37 have both), from only **75 papers** |
| B | **EDD** (duplication across images from the same paper) | **523 blot–blot pairs** (700 images), with boxes in both images |

All counts are before the western-only filter.

**Negatives:**
- **Task A:** blot images from papers with nothing flagged in IDD, CSTD or EDD (about
  19,100 images), at most 2 per paper, as `get_biofors_blots.py` already does.
- **Task B:** pairs of blots from the *same* unflagged paper. These are hard negatives:
  same lab, same imaging setup, same figure style, so "the two look alike" isn't enough to
  call a pair positive.
- "Not flagged" doesn't mean clean. You screen the dev negatives (section 2.5).

Because the task A positives cluster in 75 papers, confidence intervals are bootstrapped
by paper, and the BioFors task A arm will have wide intervals.

### Richardson & David, "Problematic images in vendor antibody verification data"

- Concept DOI `10.5281/zenodo.20402475`. Pinned version `260825` (record `22090940`,
  2026-08-25), CC-BY-4.0.
- 18,944 problematic images from 16 vendor antibody catalogs. Files: originals, annotated
  copies marking each problem, and a CSV with a free-text `summary` for each image.

**Task A: within-blot problems.** About 5,000 images.

| problem (`summary` field) | images |
|---|---|
| Apparent painting of background | ~4,710 (94%) |
| Repetitive or duplicated regions or blocks of background noise | ~230 |
| Discontinuities in the background, spliced lanes | ~30 |
| Identical or unusually similar bands (within one image) | ~10 |

- **By vendor:** Origene 2,230, Thermo Fisher 1,520, LSBio 351, Bioss 305, HUABIO 205,
  Santa Cruz 125, Abnova 120, Boster 119, Abcam 33, GeneTex 1.
- Painting dominates, so we sample **stratified by problem type**. Otherwise the score
  measures painting detection only.

**Task B: shared background templates.** About 13,900 images reuse one of 8 background
templates, often across vendors. They appear in the `summary` field as "background
pattern A–H".

| template | images | vendors |
|---|---|---|
| A | ~7,600 | G-Biosciences, Thermo Fisher, LSBio, Antibodies.com, GeneTex, Abcam |
| B | ~4,050 | G-Biosciences, LSBio, Thermo Fisher, GeneTex |
| C | ~1,000 | Thermo Fisher, R&D Systems, Abcam, Millipore Sigma, Abnova |
| D (partly matches C) | ~850 | Thermo Fisher, R&D Systems, Abcam, Millipore Sigma, Abnova |
| E | 362 | Proteogenix |
| F, G, H | 7, 5, 10 | Abcam, Thermo Fisher, Abnova |

There are also about 50 smaller groups: images "identical to image_index N" or sharing a
background with an image from another product.

- **Positive pairs:** two images from different products that share a template (or that
  the CSV says are identical). Sampled evenly across templates, so template A doesn't
  dominate, and including cross-vendor pairs.
- **Negative pairs:** two clean images scraped from the same vendor, from different
  products (section 2.2).
  - **Hard negatives** are chosen with a classical similarity score: same layout, same
    lane count, similar band positions. A negative pair should look alike at a glance, so
    Claude has to actually compare the backgrounds.
  - Some negative pairs are **one template image and one clean image**, so the comparison
    tests sharing, not just whether an image looks like a template.
- **Caveat:** with only 8 templates, Richardson task B results come from few distinct
  backgrounds. BioFors EDD, with 523 pairs from many papers, is the more varied test of
  task B. Report both.

---

## 2. Building the datasets

### 2.1 Download and pin

- BioFors archive and annotation files; Richardson `260825` (CSV, originals, annotated
  images).
- Record checksums. Raw data stays out of git.

### 2.2 Scrape Richardson negatives

1. **Check the rules first.** For each vendor, check `robots.txt` and the terms of use
   before scraping. Skip any vendor that forbids it and note that in the results.
2. **Scraper behavior.**
   - Rate-limited: one request every few seconds per vendor, with a descriptive
     user agent.
   - It caches every page, so each page is fetched once.
   - It logs the URL, catalog number, product title and fetch date for every image.
3. **Which vendors.** The vendors in either task:
   - task A: Origene, Thermo Fisher, LSBio, Bioss, HUABIO, Santa Cruz, Abnova, Boster,
     Abcam;
   - task B adds: G-Biosciences, Antibodies.com, R&D Systems, Millipore Sigma,
     Proteogenix, GeneTex.
4. **How many.** Per vendor, in proportion to that vendor's share of the positives in each
   task, about 1:1 overall. Task B negatives need at least two clean images per vendor
   from different products.
5. **Exclusions.**
   - **Exclude** every catalog number in the Richardson spreadsheet. A product with one
     flagged image is a poor source of clean images.
   - Prefer products in the same target categories as the positives (taken from product
     titles), so the "what protein is this" mix matches.
6. **Screen out known templates.** Check every scraped image against templates A–H by
   normalized cross-correlation on the background. Drop any match. These images are
   manipulated even though they aren't in the spreadsheet yet, and they would be false
   negatives in both tasks.
7. **Scrape-time copy check.** Also run a cheap pairwise background-correlation pass over
   the scraped images. Scraped images that share a background are unlisted manipulations:
   drop them, and log them as possible new findings for Richardson's submission form.

### 2.3 Western-only filter

- A Haiku pass labels each candidate image (from either source) as western blot,
  DNA/RNA gel, Coomassie/SDS-PAGE, IHC/ICC, or other.
- You review every image labeled western, plus a sample of the rest, to measure the
  classifier's error rate.
- Only images you confirm as western blots enter the dataset.

### 2.4 Single-blot crops

- **Crop rule.** One crop is one blot panel (the target strip, plus the loading control
  if it sits in the same panel). Text labels are cropped or masked: MW markers, lane
  labels, sample names, watermarks, logos. This is applied identically to positives and
  negatives.
  - BioFors images are already panel-level; we only mask text.
  - Vendor images are cropped by a detector for the blot region (Claude, or a simple
    intensity-based detector), and you check the crops.
- **Ground-truth regions.**
  - BioFors: carry the boxes through the crop transform (IDD and CSTD boxes for task A;
    EDD boxes in both images for task B).
  - Richardson: diff each annotated image against its original to find the marked region
    automatically, then check by eye. A positive crop has to contain the marked region.
    A crop that cuts the evidence off is dropped.
  - For task B template pairs, the shared region is the background outside the bands.
    Its ground truth is a mask of where the two crops match after alignment.
- **Context as text (optional condition).** Cropping removes the MW ladder, so biology
  rules about band size need another channel. For every image of both classes, store the
  target, the expected MW from the product title or UniProt, and the ladder positions
  read before cropping. Give these to Claude as text in a separate condition (task A).

### 2.5 Label check by you

- **Positives:** confirm each dev positive shows the claimed problem. For task A, use the
  contrast-stretched copy for painting. For task B pairs, use an aligned difference image.
- **Negatives:** screen every dev negative (single images and pairs) the same way.
  Anything suspicious is removed and logged.
  - Count how many you remove. That count estimates the label noise in unscreened test
    negatives.
  - Screening test negatives too would give cleaner labels. The catch: you would see test
    images, and they may then shape your rules. Since you can review as many as needed,
    the better order is to finish the rulebook first, then screen test negatives blind to
    the model's outputs.

### 2.6 Normalize and check for shortcuts

1. **Normalize** with `fake_blot_detection.images`: grayscale, fixed long side, fixed JPEG
   quality, hashed filenames.
2. **Shortcut check before any API spend.**
   - **Task A:** single-statistic AUCs (mean, std, aspect ratio, noise, entropy, dark
     fraction, JPEG quality estimate, crop size), plus each vendor's positive rate, which
     should be near 50%.
   - **Task B:** pair statistics: difference in size, aspect ratio, mean and noise level;
     whether the two crops come from the same vendor; and a plain global pixel
     correlation.
3. **Rule of thumb.** If any trivial feature separates the classes (AUC well away from
   0.5), fix the sampling before going on. Global correlation may well be informative for
   task B. That's fine, but report it as a classical baseline, not something the dataset
   should hide.

### 2.7 Split once and lock the test set

Split 50/50 into dev and test, grouped so near-copies can't land on both sides:

| task | source | grouped by |
|---|---|---|
| A | BioFors | paper |
| A | Richardson | catalog-number family or product line |
| B | BioFors | paper |
| B | Richardson | **template**, so rules can't key on what one specific template looks like. A and B are large, so one goes to each side. C/D partly match, so they go together. E–H are spread out. |

**The test set is locked.** You write rules looking only at dev.

### 2.8 Balance and sizes

**Base rate.** F1 depends on it. Use 50/50 for the main comparison, plus a re-weighted
analysis at a realistic low prevalence (for example 5%) to show what precision looks like
then.

**Test-set sizes** (dev can be as large as useful):

| task | source | test set |
|---|---|---|
| A | Richardson | about 400 images: 200 manipulated, stratified by type, with every non-painting image the filters leave; 200 clean |
| A | BioFors | all within-blot positives that survive filtering, split by paper, with an equal number of negatives |
| B | Richardson | about 300 pairs: 150 sharing a template, 150 negatives, half of them hard |
| B | BioFors | about 300 pairs: 150 EDD, 150 same-paper negatives |

---

## 3. Phase 1: Baseline (no rules)

### 3.1 Models and prompt

**Models.** Opus 5.5 (main), Sonnet 5.5 and Haiku 5.5 (cost/quality curve).

**Prompts** (versioned, like `PROMPT_VERSION` in Level 1). Each states the base rate and
asks for structured output.

Task A:

```json
{
  "reasoning": "...",
  "verdict": "manipulated" | "legitimate",
  "probability_manipulated": 0.0-1.0,
  "manipulation_type": "duplication" | "splice" | "painting" | "repeated_noise" | "none" | "other",
  "regions": [[x0, y0, x1, y1], ...]
}
```

Task B:

```json
{
  "reasoning": "...",
  "verdict": "shared_content" | "independent",
  "probability_shared": 0.0-1.0,
  "shared_what": "background" | "bands" | "whole_image" | "none",
  "regions_image_1": [[x0, y0, x1, y1], ...],
  "regions_image_2": [[x0, y0, x1, y1], ...]
}
```

### 3.2 Conditions

The conditions show where the difficulty lies.

| condition | task | what Claude sees |
|---|---|---|
| A0 | A | the crop |
| A1 | A | crop + contrast-stretched copy (Levels: raised black point, lowered white point) |
| A2 | A | A1 + horizontally flipped, vertically flipped and 180°-rotated copies |
| A3 | A | A1 + target, expected MW and ladder positions as text (section 2.4) |
| P0 | B | the two crops |
| P1 | B | both crops + contrast-stretched copies |
| P2 | B | P1 + flipped and rotated copies of image 2 (templates reappear flipped) |

A1, A2, P1 and P2 are not "rules". They are cheap image processing that makes evidence
visible. They also set a stronger baseline, so later gains can't be credited to something
this simple.

### 3.3 Classical baselines

These put the numbers in context:
- **Task A:** copy-move detection (SIFT/ORB keypoint matching plus block matching);
  local noise-variance and residual maps for painting.
- **Task B:** keypoint matching between the two crops; background noise-residual
  correlation after masking bands; global correlation.
- If it can be run, the published BioFors baseline (MONet) on the BioFors arms.

### 3.4 Retrieval-then-verify (task B, small demonstration)

This shows how task B would be used in practice, without comparing every image with every
other.

1. The classical noise-correlation step ranks, for each query image, every other image in
   a pool of about 1,000 (Richardson test templates plus scraped clean images).
2. Claude checks only each query's top k = 5 candidates.
3. Report recall at k for the classical step alone, then precision and recall after
   Claude checks.

This answers whether Claude adds anything on top of a cheap filter. Cost is k calls per
query.

### 3.5 Metrics

These extend `fake_blot_detection.metrics` and apply to both tasks.

- F1, precision and recall at Claude's own verdict.
- **F1 at a threshold calibrated on dev.** In Level 1, AUC (0.78) was far above accuracy
  (0.61) because the cutoff was in the wrong place. A calibrated threshold is a free gain,
  so the rules have to beat *calibrated* F1, not raw F1.
- ROC-AUC and PR-AUC, with 95% bootstrap CIs, grouped by paper, product or template.
- Breakdowns by source, manipulation type or template, and vendor.
- **Localization**: share of true positives whose predicted region overlaps the
  ground-truth region at IoU ≥ 0.1 (in both images for task B). The threshold is loose
  because Claude's boxes are rough. A right verdict pointing at the wrong place counts as
  a lucky guess.
- Refusal and unparseable-answer rates, recorded and never silently retried on another
  model.

### 3.6 Decision point

If the calibrated baseline F1 is already high (≥ ~0.9) for a task, source or manipulation
type, report it and focus the rules elsewhere.

---

## 4. Phase 2: Error analysis on dev (where your expertise comes in)

1. Build a review sheet of dev errors. Each row shows the crop (or both crops), the
   contrast-stretched copies, the ground-truth region, Claude's verdict, Claude's region
   and its reasoning. Task B rows also show an aligned difference image.
2. You go through false negatives and false positives and tag *why* a biologist would have
   got each one right. That gives the first list of candidate rules. You can review as
   many as needed, so review all dev errors, plus a sample of correct answers to catch
   right-for-the-wrong-reason cases.
3. Code Claude's reasoning to find its wrong beliefs. In Level 1 it read processing
   artifacts as signs of scanning or compression, and so as signs of a real image. Watch
   for the same excuse here:
   - task A: painted, flat backgrounds read as normal;
   - task B: "same vendor, same imaging system" offered to explain identical backgrounds.

---

## 5. Phase 3: Expert rules

### 5.1 Rule format

Each rule is one entry in a versioned `rules/*.yaml`, tagged with the task it applies to:

```yaml
- id: R03
  task: [A, B]
  name: Background noise should never repeat
  rationale: >
    Film grain, membrane texture and camera noise are random. Two regions with the same
    speckle pattern can't come from one exposure, or from two different exposures.
  look_for: identical speckle/texture patches, between lanes, around bands, or across the two images
  targets: [repeated_noise, duplication, template]
  false_positive_risks: [heavy JPEG blocking, very smooth overexposed backgrounds]
  needs: [contrast_stretch]
```

The `false_positive_risks` field matters as much as the rule itself. Rules that only push
toward "manipulated" will raise recall and cost precision, and can leave F1 unchanged.

### 5.2 Starter rules for you to edit, reject or replace

**Task A: image evidence**
- **Background continuity.** Real ECL/film backgrounds vary smoothly. Flat, uniform
  patches with sharp edges, especially after a contrast stretch, suggest painting.
  Painting is 94% of the Richardson task A positives, so this rule matters most.
- **Noise is random.** Repeated speckle or blocks mean copy-paste.
- **No two bands are identical.** Even replicate lanes differ in shape, edge and intensity
  profile. Bands that match after a flip or rotation are duplicated.
- **Consistent gel geometry.** Bands in neighboring lanes share the gel's smile or frown,
  tilt and migration front. One lane that ignores it suggests a splice.
- **Lane boundaries.** A sharp vertical step in background intensity or texture between
  lanes, with no gap or marker, suggests splicing.
- **Band-to-background halo.** Real bands fade into the background. A band with a crisp
  rectangular or blotchy edge on a clean field was pasted or painted.
- **Saturation consistency.** If one band is saturated, others of similar intensity on
  the same exposure should be too.

**Task A: biology and context** (in the A3-style condition, where target and MW are
given)
- Does the band size fit the target's expected molecular weight, isoforms or common
  modifications, given the ladder?
- Is the result plausible for the claimed sample? Consider tissue expression and
  knockout or knockdown lanes.
- For vendor images, can one perfectly clean band across very different lysates be
  realistic for that antibody class (polyclonal vs monoclonal)? Is the total absence of
  nonspecific bands believable?

**Task B: pairs**
- **Same equipment doesn't mean the same noise.** The same scanner, film or imager gives a
  similar overall *look* (grain size, tone, vignetting). It never gives identical speckle
  at identical positions.
- **Compare the background, not the bands.** Mentally mask the bands and compare the
  empty membrane. A template with different bands pasted in matches everywhere except
  around the bands.
- **Check after flips and rotations.** Reused content is often mirrored or rotated.
- **Membrane artifacts are fingerprints.** Bubbles, scratches, fingerprints, edge damage
  and dust in the same relative place mean the same membrane exposure.
- **Identical bands across different experiments.** Two different antibodies or lysates
  can't give pixel-identical band shapes and intensity profiles.
- **Expected biological differences.** If the two images claim different targets of
  different molecular weights, matching band positions are a warning sign, not a
  reassurance.

### 5.3 How the rules reach Claude (compare these)

| method | how it works | why test it |
|---|---|---|
| **R-prompt** | rulebook placed in the system prompt (prompt-cached) | simplest |
| **R-checklist** | Claude answers each rule `yes / no / n.a.` with evidence and region, then gives an overall verdict | forces it to actually check each rule; gives an answer per rule |
| **R-aggregate** | same checklist answers, but the verdict comes from a small logistic regression fitted on dev | interpretable weights; separates "Claude sees the cue" from "Claude weighs the cue well" |
| **R-tools** | rules that are image operations become tools Claude can call: contrast stretch, flip-and-compare, local noise-variance map, block self-similarity, and for pairs a band-masked difference image after alignment | some evidence just isn't visible to a vision model at native resolution |

### 5.4 Controls: making sure the gain comes from the biology

- **Length-matched generic prompt**: same length, generic advice ("examine carefully,
  consider all possibilities"). Rules versus this control isolates the rule content.
- **Threshold-only**: baseline with a calibrated threshold (from Phase 1).
- **Few-shot**: k labeled dev examples, no rules. Is showing examples worth more than
  explaining?
- **Leave-one-rule-out ablation** on dev: each rule's own contribution, and which rules
  cost precision.
- **Shuffled rationales** (optional): rules with mismatched rationales. Does Claude use
  the reasoning or only the keywords?

### 5.5 Overfitting protocol

- You look only at dev images and dev errors.
- Each rulebook version is frozen and given a hash before it touches test.
- Test is scored **at most once per pre-declared rulebook version**, and every version is
  reported, including those that didn't help.
- Iterating on dev (write rules, run on dev, look at errors, revise) is fine. Plan for 2–3
  rounds.
- Task B rules must be generic. Describing one specific template ("pattern A has a dark
  smudge at top left") is not allowed. The template-grouped split checks this.

---

## 6. Cost estimate

Prices (per million tokens, input / output): Opus 5.5 $4 / $20, Sonnet 5.5 $2 / $10,
Haiku 5.5 $0.10 / $0.50. The Message Batches API halves these.

**Rough tokens per call:**

| component | tokens |
|---|---|
| one 512-px image | ~250–350 (about width × height / 750) |
| task A call with contrast copy | ~1,500 input |
| task B call with contrast copies | ~2,500 input; with flipped copies ~3,500 |
| rulebook | ~2,000, cached after the first call (cache reads cost much less) |
| output, mostly Claude's reasoning at `high` effort | ~2,000–5,000 |

Output dominates. A pair call costs only about 15–30% more than a single-image call.

**Rough cost of Opus with the batch discount:**

| unit | cost |
|---|---|
| one call | about $0.03–0.06 |
| one condition over a 400-item set | about $15–25 |

**Rough run count per task:**
- about 7 baseline conditions on dev and test;
- 4 rule methods, 3 controls and an ablation of about 10 rules on dev;
- 2–3 rulebook rounds;
- a few test runs.

That comes to about 40–50 condition × set runs.

| item | Opus (batch) |
|---|---|
| task A, both sources | ~$700–1,100 |
| task B, both sources | ~$400–700 (fewer conditions: no MW-context arm) |
| retrieval-then-verify demo (about 200 queries × 5) | ~$50 |
| Sonnet runs | about half of Opus |
| Haiku runs | about 1/40 of Opus, so negligible |
| **total, all three models** | **about $1,700–2,800** |

Task B adds roughly 40% to the total, not double.

**How to cut the cost:**
- Run the ablation and early rule rounds on Sonnet, and confirm only the final rulebook
  on Opus.
- Use `medium` effort if a 30-image check shows no loss of quality.
- Shrink dev runs to 200 items during iteration.

**Before every full run, measure.** A 10-call smoke test records real input and output
tokens. Its cost projection is printed and must be approved before the batch is sent.

---

## 7. Results to report

- Baseline vs rules on F1, AUC and localization: per task, per source, per manipulation
  type or template, and per vendor. Include CIs and paired significance (McNemar on
  verdicts, paired bootstrap on AUC and F1).
- Opus vs Sonnet vs Haiku, with and without rules. Can rules let a cheaper model match
  Opus?
- Claude vs classical baselines on each task. For task B, does Claude add precision on
  top of the classical candidate filter (section 3.4)?
- Which rules helped and which hurt (ablation table).
- Whether the gain carries over:
  - rules written on Richardson dev, tested on BioFors test (vendor images vs journal
    figures), and the reverse;
  - for task B, carry-over across templates.
- Representative examples where rules fixed an error, and where they caused one.
- Label-noise estimate from your screening of the negatives, and how much it could move
  precision.

---

## 8. Infrastructure

- New package `src/manipulated_blots/` that reuses `fake_blot_detection`'s `images`,
  `metrics` and the detector pattern (installed as a dependency, or the small modules
  copied over if you'd rather keep the repos independent). The detector is extended to
  send two images for task B.
- `experiments/` scripts:
  - data: `get_biofors.py`, `get_richardson.py`, `scrape_vendors.py`;
  - filtering and cropping: `classify_assay.py`, `crop_blots.py`,
    `annotation_regions.py`;
  - pairs: `make_pairs.py` (positive, negative and hard-negative pairs),
    `template_screen.py` (background correlation against A–H and among scraped images);
  - running: `prepare.py`, `shortcut_check.py`, `run_claude.py` (resumable JSONL, like
    Level 1);
  - analysis: `analyze.py`, `review_sheet.py`, `retrieve_verify.py`.
- `rules/`: versioned YAML rulebooks.
- **Review UI**: one page for western-only confirmation, crop checks, negative screening
  and error tagging. It shows the original, the contrast stretch, the flipped copies and,
  for pairs, an aligned difference image, and writes your labels to a file.
- Use the **Message Batches API** for full runs (half price), prompt caching for the
  rulebook, and the 10-call smoke test before every full run (section 6).
- The API key is read from `BLOT_ANTHROPIC_API_KEY`, as in Level 1.

---

## 9. Milestones

| # | output | gate |
|---|---|---|
| M1a | Richardson + BioFors downloaded; task A positives and task B groups selected | counts match section 1 |
| M1b | Vendor scrape done (ToS checked, templates and copies screened out) | about 1:1 negatives per vendor |
| M1c | Western-only filter, crops, ground-truth regions, pairs built; your review of dev | labels confirmed |
| M1d | Normalized, split, shortcut checks pass | shortcut AUCs ≈ 0.5 |
| M2 | Task A baseline (A0–A3) and task B baseline (P0–P2) × 3 models; classical baselines; retrieval demo | baseline report |
| M3 | Error review sheets; you write rulebook v1 (task A and task B rules) | v1 frozen |
| M4 | Rule methods and controls on dev, then one test run per task | results report |
| M5 | 1–2 more rule rounds, cross-source and cross-template transfer, write-up | final report |

---

## 10. Decisions made

- **Tasks:** within-blot manipulation (task A) and pair verification of reuse across blots
  (task B).
- **Richardson negatives:** scraped from the same vendors' catalogs.
- **Assay:** western blots only.
- **Models:** Claude only.
- **Unit of judgment:** single blot crops; pairs of single blot crops for task B.
- **Review:** you can review as many dev images as needed.

## 11. Still open

- **Loading control:** keep a loading control in the same crop as the target band when
  they share a panel (current default), or crop to the target strip only?
- **BioFors arm size:** if the western filter leaves too few BioFors task A positives
  (fewer than about 80), report BioFors task A as a secondary, small-sample check, with
  Richardson as the main dataset.
- **Budget:** is about $1,700–2,800 of API spend acceptable? If not, the cheaper route in
  section 6 does the iteration on Sonnet and confirms on Opus, for about half that.

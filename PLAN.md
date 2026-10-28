# Plan: can Claude spot manipulation within a western blot, and can biology rules help?

Two questions, in order:

1. **Baseline.** Shown a single western blot crop, can Claude say whether it was
   manipulated *within that blot* (duplicated bands or background, a spliced lane, a painted
   background)? How good is its F1 out of the box?
2. **Expert rules.** If F1 is low, does a rulebook written from your biology knowledge
   raise it? Does the gain come from the biology itself, not from a longer prompt or a
   moved threshold?

**Scope:**
- Only manipulation that can be seen within one blot. Reuse across blots, figures or
  products is out of scope.
- Western blots only: no DNA/RNA gels, Coomassie/SDS-PAGE stains, IHC or other assays.
- Claude models only: Opus 5.5 (main), Sonnet 5.5 and Haiku 5.5.
- The unit of judgment is a single blot crop.

This is a different task from the Level 1 work in `fake-blot-detection` (AI-generated vs
real). That repo's image normalization, Claude detector, metrics and shortcut check can be
reused here (see [Infrastructure](#7-infrastructure)).

---

## 1. The data

### BioFors (Sabir et al., ICCV 2021)

- 27,440 images are labeled `Blot/Gel`. They are already cropped to one panel each.
- Within-blot ground truth, as bounding boxes:
  - **IDD**: duplication within an image;
  - **CSTD**: cut or sharp transition (splicing).
- **218 blot/gel images have IDD or CSTD annotations** (37 have both). They come from only
  **75 papers**, and some will drop out in the western-only filter.
- EDD (duplication across images) is out of scope. Those images are used neither as
  positives nor as negatives.
- **Negatives:** blot images from papers with nothing flagged in IDD, CSTD or EDD (about
  19,100 images), at most 2 per paper, as `get_biofors_blots.py` already does. "Not
  flagged" doesn't mean clean; you screen the dev negatives (section 2.5).
- Because the positives cluster in 75 papers, confidence intervals are bootstrapped by
  paper, and the BioFors arm will have wide intervals. Richardson makes up the bulk of the
  data.

### Richardson & David, "Problematic images in vendor antibody verification data"

- Concept DOI `10.5281/zenodo.20402475`. Pinned version `260825` (record `22090940`,
  2026-08-25), CC-BY-4.0. It holds 18,944 images in total.
- After dropping cross-image problems (shared "background pattern A–H" templates, images
  identical to another `image_index`, reuse across products), **about 5,000 within-blot
  images** are left. Some may still be dropped in the western-only filter.

  | problem (`summary` field) | images |
  |---|---|
  | Apparent painting of background | ~4,710 (94%) |
  | Repetitive or duplicated regions or blocks of background noise | ~230 |
  | Discontinuities in the background, spliced lanes | ~30 |
  | Identical or unusually similar bands (within one image) | ~10 |

- **By vendor:** Origene 2,230, Thermo Fisher 1,520, LSBio 351, Bioss 305, HUABIO 205,
  Santa Cruz 125, Abnova 120, Boster 119, Abcam 33, GeneTex 1.
- Painting dominates, so we sample **stratified by problem type**. Otherwise the score
  measures painting detection only. Report every type separately.
- The `annotated_images.zip` copies mark the problem regions. Localization ground truth
  comes from them (section 2.4).
- **Negatives:** scraped from the same vendors' catalogs (section 2.2).

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
3. **What to collect.** Western blot images from antibody product pages of the same 10
   vendors.
   - Sample per vendor in proportion to that vendor's share of the positives, about 1:1
     overall. Small vendors (GeneTex, Abcam) can be pooled or dropped.
   - **Exclude** every catalog number in the Richardson spreadsheet. A product with one
     flagged image is a poor source of clean images.
   - Prefer products in the same target categories as the positives (taken from product
     titles), so the "what protein is this" mix matches.
4. **Screen out known templates.** Check every scraped image against the Richardson
   background templates A–H by normalized cross-correlation on the background. Drop any
   match. These images are manipulated even though they aren't in the spreadsheet yet.

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
  - BioFors: carry the boxes through the crop transform.
  - Richardson: diff each annotated image against its original to find the marked region
    automatically, then check by eye. A positive crop has to contain the marked region.
    A crop that cuts the evidence off is dropped.
- **Context as text (optional condition).** Cropping removes the MW ladder, so biology
  rules about band size need another channel. For every image of both classes, store the
  target, the expected MW from the product title or UniProt, and the ladder positions
  read before cropping. Give these to Claude as text in a separate condition.

### 2.5 Label check by you

- **Positives:** confirm each dev positive crop shows the claimed problem. Use the
  contrast-stretched copy for painting.
- **Negatives:** screen every dev negative the same way, with the same Levels adjustment
  Richardson uses. Anything suspicious is removed and logged.
  - Count how many you remove. That count estimates the label noise in unscreened test
    negatives.
  - Screening test negatives too would give cleaner labels. The catch: you would see test
    images, and they may then shape your rules. Since you can review as many as needed,
    the better order is to finish the rulebook first, then screen test negatives blind to
    the model's outputs.

### 2.6 Normalize and check for shortcuts

1. **Normalize** with `fake_blot_detection.images`: grayscale, fixed long side, fixed JPEG
   quality, hashed filenames.
2. **Shortcut check before any API spend.** Compute single-statistic AUCs (mean, std,
   aspect ratio, noise, entropy, dark fraction, JPEG quality estimate, crop size) per
   source.
   - Vendor is a real risk: negatives were sampled per vendor, so vendor itself should not
     predict the label. Check that each vendor's positive rate is near 50%.
   - **Scrape date or image age** is another risk. Older catalog images may compress
     differently. If any trivial feature separates the classes (AUC well away from 0.5),
     fix the sampling before going on.

### 2.7 Split once and lock the test set

- Split 50/50 into dev and test, grouped by paper (BioFors) and by catalog-number family or
  product line (Richardson), so near-copies can't land on both sides.
- **The test set is locked.** You write rules looking only at dev.

### 2.8 Balance and sizes

- **Base rate.** F1 depends on it. Use 50/50 for the main comparison, plus a re-weighted
  analysis at a realistic low prevalence (for example 5%) to show what precision looks
  like then.
- **Richardson sizes:** about 400 test images (200 manipulated, stratified by type, with
  every non-painting image the filters leave; 200 clean). Dev has as many as useful;
  since your review time isn't the limit, dev can be larger.
- **BioFors sizes:** all within-blot positives that survive filtering, split by paper,
  with an equal number of negatives.

---

## 3. Phase 1: Baseline (no rules)

**Models.** Opus 5.5 (main), Sonnet 5.5 and Haiku 5.5 (cost/quality curve).

**Prompt** (versioned, like `PROMPT_VERSION` in Level 1). It states the base rate and asks
for structured output:

```json
{
  "reasoning": "...",
  "verdict": "manipulated" | "legitimate",
  "probability_manipulated": 0.0-1.0,
  "manipulation_type": "duplication" | "splice" | "painting" | "repeated_noise" | "none" | "other",
  "regions": [[x0, y0, x1, y1], ...]
}
```

**Conditions, so we know where the difficulty lies:**

| condition | what Claude sees |
|---|---|
| B0 | the crop |
| B1 | crop + contrast-stretched copy (Levels: raised black point, lowered white point) |
| B2 | B1 + horizontally flipped, vertically flipped and 180°-rotated copies |
| B3 | B1 + target, expected MW and ladder positions as text (section 2.4) |

B1 and B2 are not "rules". They are cheap image processing that makes evidence visible.
They also set a stronger baseline, so later gains can't be credited to something this
simple.

**Classical baselines** put the numbers in context:
- copy-move detection (SIFT/ORB keypoint matching plus block matching) for duplicated
  bands and noise;
- local noise-variance and residual maps for painting;
- if it can be run, the published BioFors baseline (MONet) on the BioFors arm.

**Metrics** (extend `fake_blot_detection.metrics`):
- F1, precision and recall at Claude's own verdict.
- **F1 at a threshold calibrated on dev.** In Level 1, AUC (0.78) was far above accuracy
  (0.61) because the cutoff was in the wrong place. A calibrated threshold is a free gain,
  so the rules have to beat *calibrated* F1, not raw F1.
- ROC-AUC and PR-AUC, with 95% bootstrap CIs, grouped by paper or product.
- Breakdowns by source (BioFors vs Richardson), manipulation type and vendor.
- **Localization**: share of true positives whose predicted region overlaps the
  ground-truth region at IoU ≥ 0.1, which is loose because Claude's boxes are rough. A
  right verdict pointing at the wrong place counts as a lucky guess.
- Refusal and unparseable-answer rates, recorded and never silently retried on another
  model.

**Decision point.** If the calibrated baseline F1 is already high (≥ ~0.9) for a source or
manipulation type, report it and focus the rules elsewhere.

---

## 4. Phase 2: Error analysis on dev (where your expertise comes in)

1. Build a review sheet of dev errors. Each row shows the crop, the contrast-stretched
   copy, the ground-truth region, Claude's verdict, Claude's region and its reasoning.
2. You go through false negatives and false positives and tag *why* a biologist would have
   got each one right. That gives the first list of candidate rules. You can review as
   many as needed, so review all dev errors, plus a sample of correct answers to catch
   right-for-the-wrong-reason cases.
3. Code Claude's reasoning to find its wrong beliefs. In Level 1 it read processing
   artifacts as signs of scanning or compression, and so as signs of a real image. Look
   for the same excuse for painted, flat backgrounds here.

---

## 5. Phase 3: Expert rules

### 5.1 Rule format

Each rule is one entry in a versioned `rules/*.yaml`:

```yaml
- id: R03
  name: Background noise should never repeat
  rationale: >
    Film grain, membrane texture and camera noise are random. Two regions with the same
    speckle pattern can't come from one exposure.
  look_for: identical speckle/texture patches, especially between lanes or around bands
  targets: [repeated_noise, duplication]
  false_positive_risks: [heavy JPEG blocking, very smooth overexposed backgrounds]
  needs: [contrast_stretch]
```

The `false_positive_risks` field matters as much as the rule itself. Rules that only push
toward "manipulated" will raise recall and cost precision, and can leave F1 unchanged.

### 5.2 Starter rules for you to edit, reject or replace

Image evidence:
- **Background continuity.** Real ECL/film backgrounds vary smoothly. Flat, uniform
  patches with sharp edges, especially after a contrast stretch, suggest painting.
  Painting is 94% of the Richardson positives, so this rule matters most.
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

Biology and context (used in the B3-style condition, where the target and MW are given):
- Does the band size fit the target's expected molecular weight, isoforms or common
  modifications, given the ladder?
- Is the result plausible for the claimed sample? Consider tissue expression and
  knockout or knockdown lanes.
- For vendor images, can one perfectly clean band across very different lysates be
  realistic for that antibody class (polyclonal vs monoclonal)? Is the total absence of
  nonspecific bands believable?

### 5.3 How the rules reach Claude (compare these)

| method | how it works | why test it |
|---|---|---|
| **R-prompt** | rulebook placed in the system prompt (prompt-cached) | simplest |
| **R-checklist** | Claude answers each rule `yes / no / n.a.` with evidence and region, then gives an overall verdict | forces it to actually check each rule; gives an answer per rule |
| **R-aggregate** | same checklist answers, but the verdict comes from a small logistic regression fitted on dev | interpretable weights; separates "Claude sees the cue" from "Claude weighs the cue well" |
| **R-tools** | rules that are image operations (contrast stretch, flip-and-compare, local noise-variance map, block self-similarity) become tools Claude can call | some evidence just isn't visible to a vision model at native resolution |

### 5.4 Controls: making sure the gain comes from the biology

- **Length-matched generic prompt**: same length, generic advice ("examine carefully,
  consider all possibilities"). Rules versus this control isolates the rule content.
- **Threshold-only**: baseline with a calibrated threshold (from Phase 1).
- **Few-shot**: k labeled dev examples, no rules. Is showing examples worth more than
  explaining?
- **Leave-one-rule-out ablation**: each rule's own contribution, and which rules cost
  precision.
- **Shuffled rationales** (optional): rules with mismatched rationales. Does Claude use
  the reasoning or only the keywords?

### 5.5 Overfitting protocol

- You look only at dev images and dev errors.
- Each rulebook version is frozen and given a hash before it touches test.
- Test is scored **at most once per pre-declared rulebook version**, and every version is
  reported, including those that didn't help.
- Iterating on dev (write rules, run on dev, look at errors, revise) is fine. Plan for 2–3
  rounds.

---

## 6. Results to report

- Baseline vs rules on F1, AUC and localization, per source, per manipulation type and per
  vendor, with CIs and paired significance (McNemar on verdicts, paired bootstrap on AUC
  and F1).
- Opus vs Sonnet vs Haiku, with and without rules. Can rules let a cheaper model match
  Opus?
- Which rules helped and which hurt (ablation table).
- Whether the gain carries over: rules written on Richardson dev, tested on BioFors test
  (vendor images vs journal figures), and the reverse.
- Representative examples where rules fixed an error, and where they caused one.
- Label-noise estimate from your screening of the negatives, and how much it could move
  precision.

---

## 7. Infrastructure

- New package `src/manipulated_blots/` that reuses `fake_blot_detection`'s `images`,
  `metrics` and the detector pattern (installed as a dependency, or the small modules
  copied over if you'd rather keep the repos independent).
- `experiments/` scripts:
  - data: `get_biofors.py`, `get_richardson.py`, `scrape_vendors.py`;
  - filtering and cropping: `classify_assay.py`, `crop_blots.py`,
    `annotation_regions.py`;
  - running: `prepare.py`, `shortcut_check.py`, `run_claude.py` (resumable JSONL, like
    Level 1);
  - analysis: `analyze.py`, `review_sheet.py`.
- `rules/`: versioned YAML rulebooks.
- **Review UI**: one page for western-only confirmation, crop checks, negative screening
  and error tagging. It shows the original, the contrast stretch and the flipped copies,
  and writes your labels to a file.
- Use the **Message Batches API** for full runs (half price), prompt caching for the
  rulebook, and a 10-image smoke test before every full run. Estimate cost from those 10
  calls' token counts before scaling up.
- The API key is read from `BLOT_ANTHROPIC_API_KEY`, as in Level 1.

---

## 8. Milestones

| # | output | gate |
|---|---|---|
| M1a | Richardson + BioFors downloaded; within-blot positives selected | counts per type match section 1 |
| M1b | Vendor scrape done (ToS checked, templates screened out) | about 1:1 negatives per vendor |
| M1c | Western-only filter, crops and ground-truth regions; your review of dev | labels confirmed |
| M1d | Normalized, split, shortcut check passes | shortcut AUCs ≈ 0.5 |
| M2 | Baseline B0–B3 × 3 models on dev and test; classical baselines | baseline report |
| M3 | Error review sheet; you write rulebook v1 | v1 frozen |
| M4 | Rule methods and controls on dev, then one test run | results report |
| M5 | 1–2 more rule rounds, cross-source transfer, write-up | final report |

---

## 9. Decisions made

- **Scope:** within-blot manipulation only; cross-blot reuse is excluded.
- **Richardson negatives:** scraped from the same vendors' catalogs.
- **Assay:** western blots only.
- **Models:** Claude only.
- **Unit of judgment:** single blot crops.
- **Review:** you can review as many dev images as needed.

## 10. Still open

- **Loading control:** keep a loading control in the same crop as the target band when
  they share a panel (current default), or crop to the target strip only?
- **BioFors arm size:** if the western filter leaves too few BioFors positives (fewer than
  about 80), report BioFors as a secondary, small-sample check, with Richardson as the
  main dataset.

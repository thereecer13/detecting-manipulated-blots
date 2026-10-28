# Plan: can LLMs tell manipulated western blots from legitimate ones, and can biology rules help?

Two questions, in order:

1. **Baseline.** Shown a western blot, can a vision LLM say whether it was manipulated
   (duplicated, spliced or painted)? How good is its F1 out of the box?
2. **Expert rules.** If F1 is low, does a rulebook written from your biology knowledge
   raise it? Does the gain come from the biology itself, not from a longer prompt or a
   moved threshold?

This is a different task from the Level 1 work in `fake-blot-detection` (AI-generated vs
real). That repo's image normalization, Claude detector, metrics and shortcut check can be
reused here (see [Infrastructure](#7-infrastructure)).

---

## 1. The data and what it can and can't support

### BioFors (Sabir et al., ICCV 2021)

- 47,805 images from 1,031 papers; 27,440 are labeled `Blot/Gel`.
- Manipulation ground truth comes as bounding boxes for three tasks:
  - **IDD**: duplication within an image. 74 blot images.
  - **CSTD**: cut or sharp transition (splicing). 181 blot images.
  - **EDD**: duplication across images from the same paper. 523 blot–blot pairs (700
    images).
- In total about **876 blot images are flagged**. About 19,100 blot images come from papers
  with nothing flagged.
- Strengths: positives and negatives come from the same domain (published figures), and
  regions are annotated, so we can check *where* the model points.
- Weakness: "not flagged" doesn't mean clean. Use negatives from unflagged papers only, as
  `get_biofors_blots.py` already does. Never use unflagged images from flagged papers.
  Expect a few manipulated images among the negatives anyway.

### Richardson & David Zenodo record: "Problematic images in vendor antibody verification data"

- Concept DOI `10.5281/zenodo.20402475`. Latest version `260825` (2026-08-25), CC-BY-4.0.
- **18,944 images** from 16 vendor antibody catalogs (G-Biosciences 6.4k, Thermo Fisher
  5.6k, LSBio 2.7k, Origene 2.2k, …). Files: originals (~0.5 GB), annotated copies marking
  the problem (~1.1 GB), and a CSV with a free-text `summary` for each image.
- Counts by the `summary` field:

  | problem | images | can it be seen in one image? |
  |---|---|---|
  | Background matches a shared template ("background pattern A–H") | ~13,900 (73%) | **No**: you only see it when comparing images |
  | Apparent "painting" of background | ~4,700 (25%) | Yes, especially after a contrast stretch |
  | Repetitive or duplicated regions of background noise | ~220 | Yes |
  | Bands identical after flip/rotation; images reused across products | small | Partly (within one image) or no (across products) |

- **It has positives only.** It contains no legitimate vendor blots. If we used BioFors
  blots as the negatives, the model could just learn "vendor catalog image vs. journal
  figure crop" and look good for the wrong reason. **Domain-matched negatives are the
  biggest open problem in this plan** (see [open questions](#9-decisions-i-need-from-you)).

### Consequence: two kinds of task, scored separately

| task | input | sources |
|---|---|---|
| **A. Single-image** | one blot | BioFors IDD and CSTD; Richardson painting and repeated-noise images |
| **B. Multi-image** | a pair or set of blots | BioFors EDD pairs; Richardson background-template groups |

Pooling them into one F1 would hide the main finding. A model can't flag template reuse
from one image, however good its rules.

---

## 2. Building the datasets

1. **Download and pin versions.** BioFors archive and annotations, plus Richardson
   `260825` (record the record ID and checksums). Keep the raw data out of git.
2. **Filter Richardson to western blots.** The record also contains SDS-PAGE, IHC and
   other assay images. Drop non-blots with a quick classifier pass plus spot checks by you.
3. **Find Richardson negatives** (choose one, see the open questions):
   - **(a) Matched vendor negatives**: blots from the same vendors' catalogs that are *not*
     in the spreadsheet, sampled to match vendor, size and layout. You review a sample for
     obvious problems. Check each vendor's terms before scraping.
   - **(b) Within-Richardson contrasts only**: for task B, pair two images that share a
     template (positive) against two images with different templates (negative). This
     avoids scraping but only tests whether the model can find a shared background.
   - **(c) Skip Richardson negatives**: use Richardson only to measure recall and
     localization, and use BioFors for F1.
4. **Normalize** with `fake_blot_detection.images` (grayscale, fixed long side, fixed JPEG
   quality, hashed filenames). Crop or mask vendor watermarks, logos and text labels.
   Remove catalog numbers.
5. **Shortcut check before any API spend.** Run `analyze.py`'s single-statistic AUCs
   (mean, std, aspect ratio, noise, entropy, dark fraction) and add *vendor* and *source
   dataset* as predictors. If anything trivial separates the classes, fix the data first.
6. **Split once, by group.** Split 50/50 into dev and test, grouped by paper (BioFors) and
   by template or product family (Richardson). That way no paper, template or near-copy
   sits on both sides. **The test set is locked.** You write rules looking only at dev.
7. **Fix the class balance and report it.** F1 depends on the base rate. Use 50/50 for the
   main comparison, plus one run at a realistic low prevalence (for example 5%) so we also
   report how precision behaves at that rate.

Suggested sizes for a first pass: about 300 images per arm for task A (150 manipulated,
150 clean) and about 200 pairs for task B. That gives F1 confidence intervals of about
±0.05. Scale up if the differences turn out to be small.

---

## 3. Phase 1: Baseline (no rules)

**Models.** Claude Opus 5.5 (main), Sonnet 5.5 and Haiku 5.5 (cost/quality curve).
Optionally one non-Anthropic vision model, for generality.

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

| condition | what changes |
|---|---|
| B0 | plain image |
| B1 | image plus a contrast-stretched copy (Levels: raised black point, lowered white point, as Richardson recommends) |
| B2 | B1 plus horizontally flipped, vertically flipped and 180°-rotated copies |
| B-pair | two images side by side (task B) |

B1 and B2 are not "rules". They are cheap image processing that makes some evidence
visible. They also set a stronger baseline, so later gains can't be credited to
something this simple.

**Classical baselines** put the LLM numbers in context:
- copy-move detection (SIFT/ORB keypoint matching plus block matching) for duplication;
- noise-residual and template correlation for shared backgrounds;
- if it can be run, the published BioFors baseline (MONet) on the same split.

**Metrics** (extend `fake_blot_detection.metrics`):
- F1, precision and recall at the model's own verdict.
- **F1 at a threshold calibrated on dev.** In Level 1, AUC (0.78) was far above accuracy
  (0.61) because the cutoff was in the wrong place. A calibrated threshold is a free gain,
  so the rules have to beat *calibrated* F1, not raw F1.
- ROC-AUC and PR-AUC, with 95% bootstrap CIs.
- Breakdowns by manipulation type, source and vendor.
- **Localization**: share of true positives whose predicted region overlaps the
  ground-truth box (BioFors) or the annotated region (Richardson) at IoU ≥ 0.1, which is
  loose because LLM boxes are rough. A right verdict pointing at the wrong place counts as
  a lucky guess.
- Refusal and unparseable-answer rates, recorded and never silently retried on another
  model.

**Decision point.** If the calibrated baseline F1 is already high (≥ ~0.9) on a task, skip
Phase 3 for that task and report it.

---

## 4. Phase 2: Error analysis on dev (where your expertise comes in)

1. Export the dev errors into a review sheet: image, contrast-stretched copy, ground-truth
   region, the model's verdict, its region, and its reasoning.
2. You go through false negatives and false positives and tag *why* a biologist would have
   got each one right. That gives the first list of candidate rules.
3. Code the model's reasoning (as in the Level 1 write-up) to find its wrong beliefs. In
   Level 1 it read processing artifacts as "scan/compression" and so as a sign of a real
   image. Look for similar excuses here.

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
  targets: [repeated_noise, duplication, template]
  false_positive_risks: [heavy JPEG blocking, very smooth overexposed backgrounds]
  needs: [contrast_stretch]
```

The `false_positive_risks` field matters as much as the rule itself. Rules that only push
toward "manipulated" will raise recall and cost precision, and can leave F1 unchanged.

### 5.2 Starter rules for you to edit, reject or replace

Single image:
- **Background continuity.** Real ECL/film backgrounds vary smoothly. Flat, uniform
  patches with sharp edges, especially after a contrast stretch, suggest painting.
- **Noise is random.** Repeated speckle means copy-paste.
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

Biology and context (where you know more than the model):
- Does the observed band size match the target's expected molecular weight, isoforms or
  common modifications, given the marker ladder?
- Is the result plausible for the claimed sample: knockout or knockdown lanes, tissue
  expression, a loading control that fits?
- For vendor images, does one perfectly clean band across very different lysates fit what
  that antibody class (polyclonal vs monoclonal) can realistically do?

Multi-image:
- **Shared backgrounds.** Two blots from different experiments can't share background
  texture, even if the bands differ.
- **Recurring band shapes.** The same band shape appearing across unrelated products
  suggests a stock band being reused.

### 5.3 How the rules reach the model (compare these)

| method | how it works | why test it |
|---|---|---|
| **R-prompt** | rulebook placed in the system prompt (prompt-cached) | simplest |
| **R-checklist** | the model answers each rule `yes / no / n.a.` with evidence and region, then gives an overall verdict | forces it to actually check each rule; gives an answer per rule |
| **R-aggregate** | same checklist answers, but the verdict comes from a small logistic regression fitted on dev | interpretable weights; separates "the model sees the cue" from "the model weighs the cue well" |
| **R-tools** | rules that are image operations (contrast stretch, flip-and-compare, local noise correlation) become tools the model can call | some evidence just isn't visible to a VLM at native resolution |

### 5.4 Controls: making sure the gain comes from the biology

- **Length-matched generic prompt**: same length, generic advice ("examine carefully,
  consider all possibilities"). Rules versus this control isolates the rule content.
- **Threshold-only**: baseline with a calibrated threshold (from Phase 1).
- **Few-shot**: k labeled dev examples, no rules. Is showing examples worth more than
  explaining?
- **Leave-one-rule-out ablation**: each rule's own contribution, and which rules cost
  precision.
- **Shuffled rationales** (optional): rules with mismatched rationales. Does the model use
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

- Baseline vs rules on F1, AUC and localization, per task (A/B), per source, per
  manipulation type, with CIs and paired significance (McNemar on verdicts, paired
  bootstrap on AUC and F1).
- Which rules helped and which hurt (ablation table).
- Whether the gain carries over: rules written on BioFors dev, tested on Richardson test,
  and the reverse.
- Representative examples where rules fixed an error, and where they caused one.
- An honest list of what LLMs can't do here (for example cross-image template reuse
  without retrieval).

---

## 7. Infrastructure

- New package `src/manipulated_blots/` that reuses `fake_blot_detection`'s `images`,
  `metrics` and the detector pattern (installed as a dependency, or the small modules
  copied over if you'd rather keep the repos independent).
- `experiments/`: `get_biofors.py`, `get_richardson.py`, `prepare.py`, `shortcut_check.py`,
  `run_llm.py` (resumable JSONL, like Level 1), `analyze.py`, `review_sheet.py`.
- `rules/`: versioned YAML rulebooks.
- Use the **Message Batches API** for full runs (half price), prompt caching for the
  rulebook, and a 10-image smoke test before every full run. Estimate cost from those 10
  calls' token counts before scaling up.
- The API key is read from `BLOT_ANTHROPIC_API_KEY`, as in Level 1.

---

## 8. Milestones

| # | output | gate |
|---|---|---|
| M1 | Both datasets downloaded, blot-filtered, normalized, split; shortcut check passes | shortcut AUCs ≈ 0.5 |
| M2 | Baseline B0–B2 and B-pair on dev and test; classical baselines | baseline report |
| M3 | Error review sheet; you write rulebook v1 | v1 frozen |
| M4 | Rule methods and controls on dev, then one test run | results report |
| M5 | 1–2 more rule rounds, cross-dataset transfer, write-up | final report |

---

## 9. Decisions I need from you

1. **Richardson negatives**: (a) matched vendor scrape, (b) template-pair task only, or
   (c) recall-only use? My recommendation: start with (b) plus (c) since they need no
   scraping, and add (a) for one or two vendors if the results are worth extending.
2. **Gels**: BioFors `Blot/Gel` mixes western blots with DNA/protein gels. Keep only
   westerns (manual or model-assisted filter), or keep both and report them separately?
3. **Models**: Claude only, or also a non-Anthropic model for comparison?
4. **Unit of judgment**: single panel crops (as in Level 1), or whole figure panels with
   several blots, which is closer to how a reviewer works and enables within-figure
   comparison?
5. **Your time**: roughly how many dev images can you review per round? That sets the
   dev size.

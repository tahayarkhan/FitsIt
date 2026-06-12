# FitsIt - Scope and Implementation Plan (MVP -> V1)

## 1) Executive Overview

FitsIt is a smart wardrobe app that helps users:

- Upload clothing items
- Organize items by category
- Extract dominant colors from each item image
- Generate valid outfit combinations
- Rank outfits by color compatibility
- Return top outfit recommendations

The project is delivered in two tracks:

- **MVP track (implementation now):** upload, extraction, generation, scoring, recommendations
- **V1/Advanced track (later):** semantic embeddings and learning-based reranking

This document is implementation-ready and serves as the source of truth for architecture, data contracts, and build order.

---

## 2) Architecture and Tech Stack

### Core stack (MVP)

- Frontend: React + Tailwind CSS
- Backend API: FastAPI (Python)
- Database + file storage: Supabase

### Free models/libraries used

- Color extraction: SegFormer + OpenCV + scikit-learn (KMeans)
- Optional later semantic matching: CLIP/OpenCLIP embeddings
- Optional later reranker: LightGBM or XGBoost

---

## 3) Storage and Data Contracts

### 3.1 Supabase storage bucket

- Bucket name: `clothing-images`
- Public: `true` (MVP simplicity)
- Recommended folders:

```txt
clothing-images/
  tops/
  bottoms/
  shoes/
  outerwear/
  other/
```

- Naming: `{uuid}.jpg`
- Full storage path: `{category-folder}/{uuid}.jpg`

### 3.2 Database schema

Table: `clothing_items`

```sql
id uuid primary key default gen_random_uuid(),
image_url text not null,
storage_path text not null,
category text check (category in ('top','bottom','shoes','outerwear','other')),
primary_color jsonb,
secondary_color jsonb,
dominant_rgb jsonb,
created_at timestamp default now()
```

Field notes:

- `image_url`: public Supabase URL
- `storage_path`: internal file path (example `tops/abc123.jpg`)
- `primary_color`: HSL object, example `{ "h": 210, "s": 0.4, "l": 0.6 }`
- `secondary_color`: optional secondary HSL cluster
- `dominant_rgb`: RGB object, example `{ "r": 120, "g": 150, "b": 200 }`

### 3.3 Canonical color representation

- Extraction pipeline may use RGB/LAB/LCH internally.
- Persisted API/database format should remain:
  - `primary_color` (HSL)
  - `secondary_color` (HSL, optional)
  - `dominant_rgb` (RGB)

---

## 4) MVP Build Plan

All MVP phases follow this structure:

- Goal
- Inputs
- Processing Steps
- Output Contract
- Failure/Fallback Behavior
- Deliverable

---

## Phase 1 - Core Upload System

### Goal

User uploads an image and category; item is stored and visible in wardrobe.

### Inputs

- `file` (image)
- `category` (`top`, `bottom`, `shoes`, `outerwear`, `other`)

### Processing Steps

1. Frontend submits `file + category` to backend.
2. Backend generates UUID filename.
3. Backend builds storage path `{category-folder}/{uuid}.jpg`.
4. Backend uploads to Supabase bucket `clothing-images`.
5. Backend gets `image_url` and `storage_path`.
6. Backend inserts a row into `clothing_items`.
7. Frontend fetches items and renders wardrobe grid.

### Output Contract

Initial DB insert shape:

```json
{
  "image_url": "https://...",
  "storage_path": "tops/abc123.jpg",
  "category": "top",
  "primary_color": null,
  "secondary_color": null,
  "dominant_rgb": null
}
```

### Failure/Fallback Behavior

- Invalid category -> reject request with validation error.
- Upload failure -> return API error; do not insert partial DB row.
- DB insert failure after upload -> return API error and log orphaned file path for cleanup.

### Deliverable

- Upload succeeds for valid image/category.
- Files persist in storage.
- Wardrobe UI displays stored items.

---

## Phase 2 - Color Extraction and Cleanup

### Goal

Extract dominant garment color reliably and store it in `clothing_items`.

### Inputs

- Source image (`image_url` or uploaded image bytes)
- Existing item metadata (`id`, `category`)

### Processing Steps

1. Load image.
2. Run SegFormer to create clothing mask.
3. Clean mask (remove small noisy regions).
4. Optional quality step: run background cleanup if image background is noisy.
5. Keep garment pixels only.
6. Convert pixels to LAB/RGB arrays.
7. Run KMeans on masked pixels (`k=3..5`).
8. Select largest cluster as dominant RGB.
9. Convert dominant RGB to HSL.
10. Optionally store second cluster as `secondary_color`.
11. Persist `primary_color`, `secondary_color` (optional), and `dominant_rgb`.

### Output Contract

Color update payload:

```json
{
  "primary_color": { "h": 210, "s": 0.4, "l": 0.6 },
  "secondary_color": null,
  "dominant_rgb": { "r": 120, "g": 150, "b": 200 }
}
```

### Failure/Fallback Behavior

- If extraction fails, keep upload intact and store null color fields.
- Mark item for retry instead of blocking user flow.
- Always keep original image for display; cleanup output is analysis-only.

### Deliverable

- Every item attempts extraction.
- Most items have persisted dominant color.
- Failures degrade gracefully without breaking upload/wardrobe.

---

## Phase 3 - Category Tagging

### Goal

Ensure every item has a valid category for outfit generation.

### Inputs

- `category` from upload form
- `clothing_items` rows

### Processing Steps

1. Validate category on upload.
2. Store category in DB.
3. Reject unknown values.
4. (Later) optional ML category prediction for assistive labeling.

### Output Contract

- `category` is always one of:
  - `top`
  - `bottom`
  - `shoes`
  - `outerwear`
  - `other`

### Failure/Fallback Behavior

- Missing/invalid category -> request rejected.
- No auto-category for MVP; user-selected category remains source of truth.

### Deliverable

- Category-clean dataset ready for outfit generation.

---

## Phase 4 - Outfit Generation Engine

### Goal

Generate valid outfit combinations from wardrobe inventory.

### Inputs

- Rows from `clothing_items` with valid `category`
- Color data where available

### Processing Steps

1. Query wardrobe items.
2. Group into arrays by category (`tops`, `bottoms`, `shoes`, optional `outerwear`).
3. Generate combinations:

```txt
for each top:
  for each bottom:
    for each shoe:
      create outfit
```

4. Prepare pairwise scoring features per outfit:
   - top-bottom
   - top-shoes
   - bottom-shoes

### Output Contract

```json
{
  "top": {},
  "bottom": {},
  "shoes": {},
  "features": {
    "pairs": ["top-bottom", "top-shoes", "bottom-shoes"]
  }
}
```

### Failure/Fallback Behavior

- If required categories are missing (for example no shoes), return no outfits with clear reason.
- Skip outfits that include items with invalid/missing category.

### Deliverable

- System returns all valid candidate outfits.

---

## Phase 5 - Outfit Scoring System

### Goal

Score outfits by color quality using deterministic, explainable rules.

### Inputs

- Outfit combinations from Phase 4
- Item colors from Phase 2 (`primary_color`, optionally `secondary_color`, `dominant_rgb`)

### Processing Steps

1. Convert colors to LAB/LCH for perceptual scoring.
2. Compute helper features:
   - `hue_distance_deg(a, b)`
   - `deltaE(lab1, lab2)`
   - `lightness_contrast(l1, l2)`
   - `chroma_balance(c1, c2, c3)`
   - `is_neutral(color)`
3. Score components:
   - Harmony (0-45): complementary/analogous/triadic windows
   - Contrast (0-30): lightness separation quality
   - Balance (0-15): chroma/saturation control
   - Neutrality (0-10): neutral anchor presence
4. Compute final score:

```txt
score = 0.45*harmony + 0.30*contrast + 0.15*balance + 0.10*neutrality
```

### Output Contract

```json
{
  "score": 32.4,
  "components": {
    "harmony": 38,
    "contrast": 24,
    "balance": 11,
    "neutrality": 8
  },
  "reasons": ["complementary_pair", "good_lightness_contrast", "neutral_anchor"]
}
```

### Failure/Fallback Behavior

- If full color data is unavailable, score with available features and reduce confidence.
- If no color data exists for an outfit, exclude it from top recommendations or mark as low-confidence.

### Deliverable

- Each outfit has a numeric score plus interpretable component/reason outputs.

---

## Phase 6 - Recommendations API

### Goal

Return highest-quality outfits to the user.

### Inputs

- Scored outfits from Phase 5
- `top_n` request parameter (default 5)

### Processing Steps

1. Generate outfits.
2. Score outfits.
3. Sort descending by final score.
4. Apply tie-breakers: higher harmony, then higher contrast.
5. Return top N.

### Output Contract

```json
[
  {
    "outfit": {},
    "score": 32.4,
    "components": {
      "harmony": 38,
      "contrast": 24,
      "balance": 11,
      "neutrality": 8
    },
    "reasons": ["complementary_pair", "good_lightness_contrast", "neutral_anchor"]
  }
]
```

### Failure/Fallback Behavior

- If no valid outfits exist, return empty array with message.
- If scoring service degrades, return deterministic fallback ranking (for example oldest/newest valid combinations).

### Deliverable

- User receives ranked, explainable outfit recommendations.

---

## 5) V1/Advanced Upgrades (Post-MVP)

## Phase 7 - Embedding-Based Semantic Matching (Advanced)

### Goal

Improve compatibility quality beyond color by adding semantic style similarity.

### Inputs

- Item images
- Existing rule-based features/scores

### Processing Steps

1. Encode each item image into an embedding vector (CLIP/OpenCLIP).
2. Store embedding vectors in DB.
3. Compute similarity between candidate outfit items.
4. Blend semantic similarity into final ranking.

### Output Contract

- Add semantic component to ranking payload:
  - `semantic_score`
  - `final_hybrid_score`

### Failure/Fallback Behavior

- If embedding generation fails, keep rule-based ranking active.
- Rule-based score remains system fallback and baseline.

### Deliverable

- More stylistically coherent recommendations while preserving explainability fallback.

### Optional future upgrade: ML reranker

- Train only after collecting user feedback (likes, saves, skips, worn outfits).
- Use free models: LightGBM or XGBoost.
- Input features: rule-derived + optional semantic similarity features.

---

## 6) Final Build Order and Milestones

1. Setup Supabase (DB + bucket)
2. Implement upload system
3. Persist item records
4. Display wardrobe
5. Extract color (SegFormer + KMeans, with optional cleanup)
6. Generate outfits
7. Score outfits
8. Return recommendations
9. (Post-MVP) Add embeddings and hybrid ranking

---

## 7) MVP Success Criteria

- Images upload successfully
- Clothing records persist correctly
- Colors are extracted and stored for most items
- Outfits are generated from categorized items
- Top recommendations are returned with score explanations

## Non-goals for MVP

- Full semantic style matching as primary ranker
- ML model training from scratch
- Complex personalization loops without feedback data

---

End of Scope.

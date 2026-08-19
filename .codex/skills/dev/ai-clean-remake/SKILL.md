---
name: ai-clean-remake
description: Remove AI-generated crunchiness, jagged or doubled edges, noisy micro-detail, repeated-edit residue, and degraded textures by freshly rebuilding the same image while preserving the original face or character, style, composition, pose, framing, clothing, objects, and lighting. Use when the user asks to clean, de-crunch, or remake a degraded AI image without redesigning it. Always retain the original image as the semantic and style reference, and optionally add Superpixel, Depth, coarse-structure, or 30-color controls. Do not use for style transfer, content changes, ordinary retouching, or simple sharpening/upscaling.
---

# AI Clean Remake

Rebuild a degraded AI image as a fresh clean render. Preserve **what the image is** while rejecting corrupted high-frequency pixels.

## Non-negotiable reference contract

1. Always include the original degraded image in final generation.
2. Make it Reference 1 and authoritative for identity, face, character design, rendering style, semantic content, pose, clothing, objects, exact locations, and fine design details.
3. Tell the generator to use the original as information but not copy its damaged pixels, halos, jaggies, noise, pseudo-texture, or oversharpening.
4. Use processed maps only as supplementary control references.
5. Never replace the original with a Superpixel, Depth, structure, or 30-color map. Map-only generation predictably loses face, style, and semantic detail.

## Scope

Use for requests such as:

- 「このAI画像のガビガビを直して」
- 「二重線やザラザラを消して同じ絵で描き直して」
- “remove crunchy AI texture without changing the image”
- “clean up repeated-edit artifacts”

Do not change clothes, pose, expression, background, objects, crop, or style unless the user separately requests those edits.

## Historical research reference

Read [references/initial-research-notes.md](references/initial-research-notes.md) only when revisiting the method design, comparing alternative controls, or investigating why a rule exists. It is a non-normative record of the initial research and includes unverified practitioner reports, provisional parameters, and hypotheses that were later corrected. This `SKILL.md` and the current bundled scripts always take precedence.

## Candidate routing

Honor an explicitly requested method, but still use the original as Reference 1.

When no method is specified, generate a small evidence-based candidate portfolio:

### Photoreal, live action, realistic 3D

Generate:

1. Direct candidate: original only.
2. Method 1 hybrid: original + Superpixel + Depth.

Depth did not prove uniquely better than a good structure control in the controlled evaluation, but the hybrid candidate was much more stable than direct generation alone. Keep direct as a control and select by QC.

If Depth is unavailable or its map is visibly wrong, use Method 3 hybrid instead. Do not stop and hand the missing dependency back to the user.

### Illustration, anime, cel shading, graphic artwork

Generate:

1. Direct candidate: original only.
2. Method 3 hybrid: original + Superpixel.
3. Method 4 hybrid: original + 30-color composition map.

These hybrid controls preserve face and style because the original remains present while the simplified maps stabilize clean color regions and layout.

### Method 2

Use original + Superpixel + coarse structure only when:

- the user explicitly requests Method 2,
- broad boundaries are the dominant risk, or
- the extracted structure map passes visual QC.

Do not make Method 2 the illustration default. A sparse or noisy structure map can misdirect the generator.

## Reference order by method

Keep this order and state each role explicitly in the generation prompt.

| Route | References |
|---|---|
| Direct | 1. original |
| Method 1 | 1. original, 2. Superpixel color-region map, 3. relative Depth map |
| Method 2 | 1. original, 2. Superpixel color-region map, 3. coarse-structure map |
| Method 3 | 1. original, 2. Superpixel color-region map |
| Method 4 | 1. original, 2. 30-color composition map |

Accept aliases:

- `1`, `M1`, `method 1`, `superpixel+depth`, `depth`
- `2`, `M2`, `method 2`, `superpixel+structure`, `structure`
- `3`, `M3`, `method 3`, `superpixel only`, `SLIC only`
- `4`, `M4`, `method 4`, `30 colors`, `30色`, `composition map`

## Workspace and source handling

1. Inspect the original visually before processing.
2. Work in a dedicated temporary or output directory.
3. Never overwrite or delete the original.
4. Preserve aspect ratio, crop, orientation, and framing.
5. Follow the available image-generation skill's output and metadata contract.

## Create deterministic control maps

Use the bundled script instead of rewriting preprocessing code:

```bash
uv run \
  --with pillow \
  --with numpy \
  --with scikit-image \
  scripts/make_controls.py SOURCE_IMAGE WORK_DIR --methods 1,2,3,4
```

Run it from this Skill directory or use an absolute script path.

Outputs:

- `01_color_region_map.png` for Methods 1–3
- `02_coarse_structure_map.png` for Method 2
- `04_composition_map_30c.png` for Method 4
- `controls.json` with parameters and paths

Useful overrides:

```bash
--methods 1,3
--segments 320
--colors 30
```

Do not sharpen control maps. Do not derive raw edges from an unsmoothed source.

## Create Depth on Apple Silicon

Use the bundled Core ML runner on macOS:

```bash
uv run \
  --python 3.12 \
  --with coremltools \
  --with huggingface-hub \
  --with pillow \
  --with numpy \
  scripts/make_depth.py SOURCE_IMAGE WORK_DIR/03_depth_geometry_map.png
```

The first run automatically downloads Apple's `coreml-depth-anything-v2-small` model from Hugging Face. Later runs reuse the Hugging Face cache.

If the automatic download or Core ML execution fails:

1. Record the failure briefly.
2. Continue with Direct + Method 3 or Method 4 hybrid.
3. Do not pretend Method 1 ran.
4. Do not block the entire clean-remake task.

## Control-map QC gate

Inspect every control before generation.

Accept a Superpixel map only if it retains:

- subject and object silhouettes,
- placement and relative scale,
- dominant color regions,
- major overlaps and lighting masses,
- no obvious source chatter.

Accept a Depth map only if foreground, subject, midground, and background ordering are visually plausible. Reject it when limbs, transparent objects, mirrors, flat artwork, or architecture produce misleading depth.

Accept a coarse-structure map only if it contains broad continuous boundaries without raw hair, fabric, foliage, or compression noise. Exclude Method 2 when the map is sparse, fragmented, or dominated by artifacts.

Accept a 30-color map only if important silhouettes, major colors, and object positions survive. Minor color loss is expected; the original supplies exact style and detail.

## Fresh-generation instruction

Adapt this template to the image and selected method:

```text
Reconstruct the same image as a completely fresh, clean render.

Reference 1 is the degraded original and is authoritative for facial or character identity, rendering style, semantic content, pose, clothing, object inventory, exact locations, fine design details, crop, and aspect ratio. Use it as information, but do not copy its damaged pixels or artifacts.

[State the exact role of every supplementary reference.]

Strictly preserve composition, camera, framing, subject placement and scale, pose, head direction, expression, hairstyle shape, clothing design, objects, foreground/midground/background relationships, lighting direction, dominant colors, and rendering category.

Discard doubled contours, black or white halos, jagged edges, ringing, oversharpening, noisy micro-detail, dirty pseudo-texture, malformed small details, compression residue, and repeated-edit artifacts. Reconstruct clean coherent detail from scratch.

Do not redesign, beautify, restyle, add, remove, or replace content. Do not imitate the posterized, mosaic, grayscale-depth, or line-map appearance of supplementary references.
```

Append one method role:

- Method 1: Reference 2 controls clean color regions and composition. Reference 3 controls relative depth, perspective, and spatial ordering only.
- Method 2: Reference 2 controls clean color regions and composition. Reference 3 controls broad silhouette and meaningful boundaries only.
- Method 3: Reference 2 controls clean color regions, silhouette, layout, and lighting masses only.
- Method 4: Reference 2 controls broad color placement, silhouette, scale, overlaps, and camera geometry only.

## Quality control

Compare every candidate with the original. Do not select by method name.

Reject a candidate if any gate fails:

### Artifact removal

- doubled or crunchy contours remain,
- halos, ringing, high-frequency chatter, or dirty pseudo-texture remain,
- the candidate merely smooths or sharpens the damaged pixels.

### Identity and style

- face or recognizable character changes materially,
- photoreal becomes illustrative or illustration becomes photoreal,
- cel shading becomes painterly,
- clothing design, hair shape, or distinctive rendering language changes.

### Composition and semantics

- crop, camera, pose, placement, scale, or gaze changes,
- objects move, disappear, appear, or change category,
- foreground/background ordering or major lighting changes.

Select the candidate that best satisfies all gates, not the cleanest-looking candidate in isolation.

## Retry

Perform at most two automatic retries unless the user asks for more.

- If artifacts remain, strengthen the instruction not to copy damaged pixels and simplify the control slightly.
- If identity or style drifts, strengthen Reference 1's authoritative role. Never remove it.
- If composition drifts, use a valid supplementary control or generate another candidate of the best-performing route.
- If Depth distorts geometry, fall back to Method 3 or Method 4 hybrid.
- If structure lines misdirect generation, exclude Method 2 rather than adding more noisy lines.

## Output

Return:

- the selected cleaned image,
- the selected route in one short sentence,
- intermediate maps only when useful for debugging or requested,
- any fallback that changed the requested method.

When the user asks to compare methods, keep the original present in every non-direct method, keep generation instructions otherwise identical, label outputs, and visually compare them before claiming a winner.

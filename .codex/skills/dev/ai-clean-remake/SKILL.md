---
name: ai-clean-remake
description: Remove AI-generated crunchiness, jagged/doubled edges, noisy micro-detail, repeated-edit artifacts, and degraded textures by rebuilding the same image from low-information structural references. Use when the user asks to clean up an AI image while preserving composition, subject, pose, framing, clothing, objects, lighting direction, and overall appearance. Supports four selectable reconstruction methods. Default to Method 1 for photoreal/live-action images and Method 2 for illustrations/anime/CG artwork. Do not use for style transfer, redesign, content changes, ordinary beauty retouching, or simple sharpening/upscaling.
---

# AI Clean Remake

Remove AI-specific visual degradation by **discarding corrupted high-frequency image information before regeneration**.

This skill is not a normal upscaler and not a sharpening workflow. The goal is:

> preserve WHAT and WHERE, discard degraded HOW, then render the same image cleanly from fresh detail.

The source image is the truth for composition and content, but its noisy edges and micro-textures must not be inherited into the final render.

## Trigger examples

Use this skill for requests such as:

- "このAI画像のガビガビを直して"
- "AI画像クリーンリメイクして"
- "二重線やザラザラを消して同じ絵で描き直して"
- "clean up AI artifacts without changing the image"
- "remove crunchy AI texture"
- "rebuild this generated image cleanly"
- "fix repeated-edit artifacts"

Do not trigger for:

- changing clothes, pose, background, objects, or expression
- style transfer
- ordinary photo restoration of a scanned/old photograph
- simple enlargement where the source is already clean
- requests whose primary goal is editing content rather than removing AI artifacts

---

# Core rule

**Do not feed the degraded source back as the primary rendering reference.**

First create one or more deliberately low-information control images that retain scene structure but destroy the high-frequency artifacts. Use those controls for fresh generation.

The original source may be used for:
1. deciding which method to use,
2. describing exact semantic content,
3. final fidelity/QC comparison,
4. optional identity assistance only when absolutely necessary and supported by the image tool.

Do not use the original source as the primary texture/detail reference during regeneration.

---

# Method selection

The user may explicitly request `method 1`, `method 2`, `method 3`, or `method 4`.

If the user does not specify a method, choose automatically:

## Method 1 — Superpixel + Depth
**Default for photoreal / live-action / realistic 3D renders.**

Use when:
- the image is photographic or strongly photorealistic
- perspective and spatial geometry matter
- a person, room, street, product, vehicle, or real-world scene needs to retain shape and depth
- AI artifacts are visible in hair, fabric, skin, background edges, or repeated edits

Intermediate controls:
1. low-frequency SLIC superpixel color/region map
2. depth/geometry map

## Method 2 — Superpixel + Coarse Structure
**Default for illustration / anime / manga-color / stylized CG / flat artwork.**

Use when:
- the image is drawn or stylized
- depth estimation may misread flat graphic structure
- preserving silhouette, broad internal boundaries, and color regions matters more than physical depth

Intermediate controls:
1. low-frequency SLIC superpixel color/region map
2. artifact-resistant coarse structure map

## Method 3 — Superpixel Only
Use when:
- a simpler workflow is requested
- artifact removal matters more than exact fine geometry
- Method 1 or 2 overconstrains the regeneration
- depth/structure extraction is unavailable or unreliable

Intermediate control:
1. low-frequency SLIC superpixel color/region map

## Method 4 — Fixed 30-Color Composition Map
Use when:
- the user explicitly wants the approximately-30-color composition-map approach
- a baseline is needed for comparison
- external dependencies for SLIC/depth are undesirable

Intermediate control:
1. exactly 30-color composition map after mild denoising/smoothing

---

# Automatic visual classification

Before preprocessing, inspect the image.

Choose **Method 1** if photographic cues dominate:
- realistic optics, skin, materials, lighting, lens behavior, depth, real-world perspective

Choose **Method 2** if illustration cues dominate:
- drawn outlines, cel shading, graphic flat colors, painterly rendering, anime/manga conventions, non-photographic stylization

For mixed media:
- realistic 3D / realistic AI portrait -> Method 1
- anime with realistic lighting -> Method 2
- photographed illustration/poster -> classify the depicted artwork, not the camera capture

If genuinely ambiguous, choose Method 1 when geometry is the bigger risk; otherwise Method 2.

Do not ask the user to choose unless they explicitly want manual control.

---

# Shared preprocessing rules

Work on a copy. Never overwrite the source.

Create a dedicated temporary work directory, for example:

`./ai-clean-remake-work/`

Preserve the original aspect ratio.

Do not crop, rotate, perspective-correct, or reframe unless the source itself contains accidental borders that the user explicitly asks to remove.

Before creating any control map:
1. apply light denoising if needed,
2. apply low-pass smoothing sufficient to suppress 1–3 px AI chatter,
3. avoid sharpening,
4. avoid raw edge extraction from the unfiltered source.

The control image should retain:
- subject position
- subject scale
- silhouette
- major limb/body placement
- major object position
- major overlap relationships
- foreground/midground/background layout
- dominant color regions
- major lighting masses

The control image should destroy:
- doubled contours
- hair-like noise unrelated to actual hair
- tiny pseudo-textures
- ringing
- jaggies
- compression residue
- repeated-edit grain
- meaningless micro-lines
- oversharpened pores/fabric
- unstable tiny background detail

---

# Method 1 procedure — Superpixel + Depth

## 1A. Create COLOR_REGION_MAP

Preferred implementation:
- Python
- Pillow/OpenCV for image IO and blur
- `skimage.segmentation.slic` for superpixels

Starting parameters are adaptive, not sacred constants.

1. Convert to a perceptually reasonable color space if practical (Lab preferred for clustering).
2. Apply Gaussian blur before SLIC.
   - starting sigma: about `0.004–0.010 × min(width, height)`
   - clamp to a practical range such as roughly 2–12 px for ordinary images
3. Run SLIC on the blurred image.
4. Replace each superpixel with its mean or median color.
5. Do not draw superpixel borders.
6. If the map still contains noisy tiny regions, reduce segment count or increase blur.
7. If important body/object boundaries disappear, increase segment count slightly.

Practical starting range:
- about 180–450 segments around 1 megapixel
- fewer for simple scenes
- more for crowded scenes

Save as:
`01_color_region_map.png`

## 1B. Create DEPTH_GEOMETRY_MAP

Prefer an available modern monocular depth estimator, with **Depth Anything V2** preferred when already available in the environment.

Requirements:
- generate a smooth relative-depth map
- normalize to a clear grayscale representation
- preserve large foreground/background separations
- do not add edge sharpening
- do not treat tiny source artifacts as geometry

Save as:
`02_depth_geometry_map.png`

If no usable depth estimator exists:
- if Method 1 was automatically selected, fall back to Method 2
- if the user explicitly demanded Method 1, report that the depth dependency is unavailable rather than pretending Method 1 was executed

## 1C. Generation roles

Use:
- `01_color_region_map.png` for composition, major color regions, placement, relative scale
- `02_depth_geometry_map.png` for geometry, depth ordering, broad shape and perspective

Do not ask the model to reproduce the visual style of either map.

---

# Method 2 procedure — Superpixel + Coarse Structure

## 2A. Create COLOR_REGION_MAP

Create the same SLIC color/region map as Method 1.

Save as:
`01_color_region_map.png`

## 2B. Create COARSE_STRUCTURE_MAP

Goal:
retain broad silhouette and meaningful internal structure without reintroducing raw artifact edges.

Do **not** run Canny or a similar detector directly on the original degraded image.

Preferred robust procedure:

1. Convert to grayscale/luminance.
2. Downsample to roughly 25–40% linear resolution.
3. Apply Gaussian smoothing.
4. Derive broad structure using either:
   - Difference of Gaussians at coarse scales, or
   - gradient magnitude/Sobel after heavy smoothing.
5. Suppress tiny connected components and isolated short lines.
6. Prefer broad, continuous structural boundaries over thin noisy detail.
7. Upscale back to original dimensions with smooth interpolation.
8. Keep the map simple and low-information.

The structure map should show:
- outer silhouette
- face/head orientation at broad level
- major clothing divisions
- large object boundaries
- strong foreground/background separators

It should not show:
- individual hair noise
- pores
- fabric microtexture
- tiny eyelashes
- repeated-edit chatter
- decorative texture unless essential to object identity

Save as:
`02_coarse_structure_map.png`

## 2C. Generation roles

Use:
- `01_color_region_map.png` for dominant colors, composition, object regions
- `02_coarse_structure_map.png` for silhouette and broad internal geometry

For illustrations, preserve the source's rendering category:
- cel-shaded stays cel-shaded
- painterly stays painterly
- line-art-heavy work may regain clean intentional lines during regeneration

Do not reproduce degraded source line quality.

---

# Method 3 procedure — Superpixel Only

Create only:
`01_color_region_map.png`

Use the Method 1/2 SLIC procedure.

Bias toward enough simplification that visible AI chatter is absent.

This method intentionally gives the generator more freedom to reconstruct fine geometry.

Use when:
- Method 1 creates depth-induced deformation
- Method 2 preserves too much incorrect structure
- the source scene is simple
- fast comparison is desired

---

# Method 4 procedure — Fixed 30-Color Composition Map

Create a single simplified composition map.

1. Apply light denoising.
2. Apply mild Gaussian smoothing before quantization.
3. Quantize to **exactly 30 colors**.
4. Prefer perceptual/Lab-space clustering or a high-quality palette quantizer.
5. Do not use dithering.
6. Do not sharpen after quantization.
7. Keep only large color masses and composition.

Save as:
`01_composition_map_30c.png`

If quantization leaves tiny speckled islands:
- clean tiny isolated regions with a mild spatial smoothing/morphological pass
- keep the palette at 30 colors

Do not silently change the requested 30-color baseline into another palette size.

---

# Fresh-generation prompt

Use the following intent when sending the control map(s) to the available image-generation/editing capability.

Adapt reference names to the selected method.

## Shared generation instruction

Reconstruct the same image as a completely fresh, clean render.

The provided control image(s) are **structural controls**, not finished artwork and not style references.

Strictly preserve:
- original composition
- framing and crop
- camera position and viewing angle
- subject placement and relative scale
- pose and body orientation
- facial direction and expression
- hairstyle shape
- clothing design
- object inventory and placement
- foreground/midground/background relationships
- broad lighting direction
- dominant color relationships
- aspect ratio

Do not redesign, beautify, restyle, add, remove, or replace scene content.

Rebuild all fine visual detail from scratch.

Do not reproduce:
- jagged AI contours
- doubled edges
- crunchy micro-detail
- ringing
- oversharpening
- dirty pseudo-texture
- repeated-edit residue
- broken hair strands
- malformed tiny background detail
- compression-like noise
- unstable high-frequency artifacts

Do not sharpen the control maps.
Do not trace their simplified edges literally.
Do not imitate posterization, superpixel boundaries, depth-map appearance, or structure-map appearance.

The controls define **WHAT, WHERE, SHAPE, DEPTH, and broad COLOR**, not final pixel texture.

The final result should look like this exact scene was generated correctly in one clean pass, with coherent fresh detail and no inherited AI degradation.

---

# Method-specific role text

Append the relevant role definition.

## Method 1
Reference 1 = COLOR/REGION CONTROL.
Use it for composition, placement, dominant color masses, scale, and region layout.

Reference 2 = DEPTH/GEOMETRY CONTROL.
Use it for depth ordering, perspective, broad geometry, and shape.

Do not visually blend the two maps. Treat them as separate control channels.

## Method 2
Reference 1 = COLOR/REGION CONTROL.
Use it for composition, placement, dominant color masses, scale, and region layout.

Reference 2 = COARSE STRUCTURE CONTROL.
Use it only for silhouette and broad meaningful boundaries.

Do not copy thin or noisy linework from the source.

## Method 3
The reference is a COLOR/REGION CONTROL only.
Use it for composition and dominant regions. Infer clean fine geometry naturally.

## Method 4
The reference is a 30-COLOR COMPOSITION MAP.
Use it only for composition, silhouette, major overlaps, relative scale, and broad color placement.
Do not imitate its posterized appearance.

---

# Optional identity assistance

The default is **not** to use the degraded source during final generation.

If the result preserves composition but materially changes a recognizable face or unique character identity:

1. Prefer a separate clean identity reference if the user supplied one.
2. If the only identity reference is the degraded source and the generation system accepts multiple role-separated references, the source may be added as a **secondary identity-only reference**.
3. Explicitly state that it is for facial/character identity and clothing specifics only.
4. The processed map(s) remain the primary structure controls.
5. Tell the generator not to inherit texture, edges, noise, or rendering artifacts from the identity reference.

Do not use this identity-assist path unless fidelity actually requires it.

---

# Quality control

After generation, compare the output against the original source.

Evaluate separately:

## A. Artifact removal
Fail if the result still contains:
- doubled contours
- crunchy edges
- high-frequency AI chatter
- dirty synthetic texture
- obvious repeated-edit residue

## B. Composition fidelity
Fail if:
- crop/framing changes materially
- subject shifts or changes scale
- pose changes
- major objects move/disappear
- camera angle changes
- foreground/background ordering changes

## C. Semantic fidelity
Fail if:
- clothing design changes
- expression changes materially
- objects are added/removed
- hairstyle changes substantially
- scene meaning changes

## D. Style/category fidelity
Fail if:
- photoreal becomes illustrative
- illustration becomes photoreal
- cel shading becomes painterly
- major rendering category changes unintentionally

---

# Retry strategy

Do not immediately add more prompt text. First adjust the intermediate representation.

If artifacts survive:
- increase pre-blur slightly
- reduce SLIC segment count
- simplify the structure map
- for Method 4, clean small palette islands more aggressively

If composition drifts:
- Method 1: strengthen/use a cleaner depth map
- Method 2: retain slightly more broad structure
- Method 3: switch to Method 1 for photoreal or Method 2 for illustration
- Method 4: consider switching to Method 1 or 2

If identity drifts while structure is correct:
- use optional identity assistance rather than feeding the full source back as the main reference

If Method 1 depth causes distortions:
- switch to Method 2

If Method 2 structure preserves bad artifact lines:
- blur/downsample more before structure extraction, or switch to Method 3

Perform at most two automatic reconstruction retries unless the user asks for more iterations.

---

# Output behavior

When successful, return:
- the cleaned final image
- the selected method, stated briefly
- optionally the intermediate control maps when useful for debugging/comparison

Do not burden the user with implementation details unless they ask.

If the user explicitly asks to compare methods:
- run the requested methods from the same source
- keep all generation instructions otherwise identical
- label outputs clearly as Method 1/2/3/4
- do not claim one is better until visually compared

---

# Method aliases

Accept these aliases:

- `1`, `M1`, `method 1`, `superpixel+depth`, `depth`
- `2`, `M2`, `method 2`, `superpixel+structure`, `structure`
- `3`, `M3`, `method 3`, `superpixel only`, `SLIC only`
- `4`, `M4`, `method 4`, `30 colors`, `30色`, `composition map`

Default routing:
- photoreal / 実写 -> **Method 1**
- illustration / イラスト / anime -> **Method 2**

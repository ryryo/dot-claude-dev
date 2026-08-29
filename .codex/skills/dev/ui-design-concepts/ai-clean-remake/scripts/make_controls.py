#!/usr/bin/env python3
"""Create deterministic low-information controls for AI clean remaking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

METHODS = {"1", "2", "3", "4"}


def save_rgb(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, format="PNG", optimize=True)


def superpixel_map(image: Image.Image, segments: int) -> Image.Image:
    from skimage.segmentation import slic

    rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    blur_radius = max(2.0, min(image.size) * 0.005)
    blurred = np.asarray(
        image.filter(ImageFilter.GaussianBlur(radius=blur_radius)),
        dtype=np.float32,
    ) / 255.0
    labels = slic(
        blurred,
        n_segments=segments,
        compactness=10.0,
        sigma=0,
        start_label=0,
        channel_axis=-1,
    )
    output = np.zeros_like(rgb)
    for label_id in range(int(labels.max()) + 1):
        mask = labels == label_id
        if mask.any():
            output[mask] = np.median(rgb[mask], axis=0)
    return Image.fromarray(np.clip(output * 255, 0, 255).astype(np.uint8), mode="RGB")


def remove_small_components(mask: np.ndarray, minimum_size: int) -> np.ndarray:
    from skimage.measure import label

    labels = label(mask, connectivity=2)
    counts = np.bincount(labels.ravel())
    keep = counts >= minimum_size
    keep[0] = False
    return keep[labels]


def coarse_structure_map(image: Image.Image) -> Image.Image:
    from skimage.feature import canny
    from skimage.morphology import closing, dilation, disk

    width, height = image.size
    scale = min(1.0, 512 / max(width, height))
    low = image.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.Resampling.LANCZOS,
    )
    low = ImageOps.grayscale(low).filter(ImageFilter.GaussianBlur(radius=2.4))
    luminance = np.asarray(low, dtype=np.float32) / 255.0
    edges = canny(luminance, sigma=1.8, low_threshold=0.035, high_threshold=0.10)
    edges = remove_small_components(edges, minimum_size=20)
    edges = closing(edges, footprint=disk(1))
    edges = dilation(edges, footprint=disk(1))
    broad = np.where(edges, 28, 246).astype(np.uint8)
    structure = Image.fromarray(broad, mode="L").filter(ImageFilter.GaussianBlur(0.6))
    return structure.resize((width, height), Image.Resampling.BICUBIC).convert("RGB")


def composition_map(image: Image.Image, colors: int) -> Image.Image:
    width, height = image.size
    scale = min(1.0, 640 / max(width, height))
    low = image.resize(
        (max(1, round(width * scale)), max(1, round(height * scale))),
        Image.Resampling.LANCZOS,
    )
    low = low.filter(ImageFilter.GaussianBlur(radius=max(1.2, min(low.size) * 0.006)))
    mapped = low.quantize(
        colors=colors,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).convert("RGB")
    return mapped.resize((width, height), Image.Resampling.BICUBIC)


def parse_methods(value: str) -> set[str]:
    methods = {part.strip() for part in value.split(",") if part.strip()}
    invalid = methods - METHODS
    if invalid or not methods:
        raise argparse.ArgumentTypeError("methods must be a comma-separated subset of 1,2,3,4")
    return methods


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--methods", type=parse_methods, default=METHODS)
    parser.add_argument("--segments", type=int, default=320)
    parser.add_argument("--colors", type=int, default=30)
    args = parser.parse_args()

    if args.segments < 40:
        parser.error("--segments must be at least 40")
    if not 2 <= args.colors <= 256:
        parser.error("--colors must be between 2 and 256")

    source = ImageOps.exif_transpose(Image.open(args.source)).convert("RGB")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}

    if args.methods & {"1", "2", "3"}:
        path = args.output_dir / "01_color_region_map.png"
        save_rgb(superpixel_map(source, args.segments), path)
        outputs["color_region_map"] = str(path)
    if "2" in args.methods:
        path = args.output_dir / "02_coarse_structure_map.png"
        save_rgb(coarse_structure_map(source), path)
        outputs["coarse_structure_map"] = str(path)
    if "4" in args.methods:
        path = args.output_dir / "04_composition_map_30c.png"
        save_rgb(composition_map(source, args.colors), path)
        outputs["composition_map"] = str(path)

    manifest = {
        "source": str(args.source.resolve()),
        "methods": sorted(args.methods),
        "segments": args.segments,
        "colors": args.colors,
        "outputs": outputs,
    }
    (args.output_dir / "controls.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()

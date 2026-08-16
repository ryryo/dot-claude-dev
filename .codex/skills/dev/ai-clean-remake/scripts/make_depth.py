#!/usr/bin/env python3
"""Generate a relative-depth control with Apple's Depth Anything V2 Core ML model."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import time
from pathlib import Path

import coremltools as ct
import numpy as np
from huggingface_hub import snapshot_download
from PIL import Image, ImageOps

MODEL_REPO = "apple/coreml-depth-anything-v2-small"
MODEL_PACKAGE = "DepthAnythingV2SmallF16P6.mlpackage"


def resolve_model(explicit_model: Path | None, revision: str) -> Path:
    if explicit_model:
        model = explicit_model.expanduser().resolve()
        if not model.exists():
            raise FileNotFoundError(f"Core ML model not found: {model}")
        return model

    snapshot = Path(
        snapshot_download(
            repo_id=MODEL_REPO,
            revision=revision,
            allow_patterns=[f"{MODEL_PACKAGE}/**"],
        )
    )
    snapshot_model = snapshot / MODEL_PACKAGE
    if not snapshot_model.exists():
        raise FileNotFoundError(f"Downloaded snapshot did not contain {MODEL_PACKAGE}")

    # Hugging Face snapshots use symlinks into the blob cache. Core ML's compiler
    # cannot reliably resolve those package-internal links, so materialize a real
    # copy in this Skill's dedicated user cache.
    cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    model = cache_base / "ai-clean-remake" / "models" / snapshot.name / MODEL_PACKAGE
    if not model.exists():
        model.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(snapshot_model, model, symlinks=False)
    return model


def normalize_depth(value: object) -> Image.Image:
    if isinstance(value, Image.Image):
        array = np.asarray(value, dtype=np.float32)
    else:
        array = np.asarray(value, dtype=np.float32).squeeze()
    low, high = np.percentile(array, [1, 99])
    normalized = np.clip((array - low) / max(high - low, 1e-6), 0, 1)
    return Image.fromarray(np.round(normalized * 255).astype(np.uint8), mode="L")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--revision", default="main")
    args = parser.parse_args()

    if platform.system() != "Darwin":
        parser.error("this Core ML depth runner requires macOS")

    model_path = resolve_model(args.model, args.revision)
    source = ImageOps.exif_transpose(Image.open(args.source)).convert("RGB")
    original_size = source.size
    portrait = original_size[1] > original_size[0]
    working = source.rotate(-90, expand=True) if portrait else source
    working = ImageOps.fit(working, (518, 392), method=Image.Resampling.LANCZOS)

    load_started = time.perf_counter()
    model = ct.models.MLModel(str(model_path), compute_units=ct.ComputeUnit.ALL)
    load_seconds = time.perf_counter() - load_started

    inference_started = time.perf_counter()
    result = model.predict({"image": working})["depth"]
    inference_seconds = time.perf_counter() - inference_started

    depth = normalize_depth(result).convert("RGB")
    if portrait:
        depth = depth.rotate(90, expand=True)
    depth = depth.resize(original_size, Image.Resampling.BICUBIC)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    depth.save(args.output, format="PNG", optimize=True)

    print(
        json.dumps(
            {
                "model": str(model_path),
                "output": str(args.output),
                "model_load_seconds": round(load_seconds, 4),
                "inference_seconds": round(inference_seconds, 4),
            }
        )
    )


if __name__ == "__main__":
    main()

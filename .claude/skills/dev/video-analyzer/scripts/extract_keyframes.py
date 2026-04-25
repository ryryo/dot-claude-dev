#!/usr/bin/env python3
"""
Video Keyframe Extraction Script

Extracts unique keyframes from a video file based on frame similarity.
Optimized for Claude Code analysis with reduced file sizes.

Usage:
    python extract_keyframes.py <video_path> [options]

Options:
    --output, -o      Output directory (default: ./keyframes/<video_name>_<timestamp>/)
    --threshold, -t   Similarity threshold (0.0-1.0, default: 0.85)
    --quality, -q     JPEG quality (1-100, default: 30)
    --scale, -s       Scale factor (0.1-1.0, default: 0.3)
    --max-frames, -m  Maximum frames to extract (default: unlimited)
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Error: Missing required dependency: {e}")
    print("\nPlease install dependencies:")
    print("  pip install opencv-python numpy Pillow")
    print("\nOr install from requirements.txt:")
    print("  pip install -r skills/video-analyzer/requirements.txt")
    sys.exit(1)


def calculate_similarity(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    Calculate structural similarity between two frames using histogram comparison.

    Args:
        frame1: First frame (BGR format)
        frame2: Second frame (BGR format)

    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Convert to grayscale for comparison
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Calculate histograms
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])

    # Normalize histograms
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    # Compare using correlation method
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    return max(0.0, similarity)  # Ensure non-negative


def extract_keyframes(
    video_path: str,
    output_dir: str,
    threshold: float = 0.85,
    quality: int = 30,
    scale: float = 0.3,
    max_frames: int = None
) -> dict:
    """
    Extract keyframes from a video file.

    Args:
        video_path: Path to the input video file
        output_dir: Directory to save extracted keyframes
        threshold: Similarity threshold (frames below this are considered keyframes)
        quality: JPEG compression quality (1-100)
        scale: Scale factor for output images (0.1-1.0)
        max_frames: Maximum number of frames to extract (None for unlimited)

    Returns:
        Dictionary with extraction statistics
    """
    # Validate video file
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Calculate output dimensions
    out_width = int(width * scale)
    out_height = int(height * scale)

    keyframes = []
    prev_frame = None
    frame_number = 0
    extracted_count = 0
    total_size = 0

    print(f"Processing video: {video_path}")
    print(f"  Duration: {duration:.2f}s ({total_frames} frames @ {fps:.2f} FPS)")
    print(f"  Original size: {width}x{height}")
    print(f"  Output size: {out_width}x{out_height}")
    print(f"  Threshold: {threshold}, Quality: {quality}, Scale: {scale}")
    print()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        is_keyframe = False

        if prev_frame is None:
            # First frame is always a keyframe
            is_keyframe = True
        else:
            # Compare with previous frame
            similarity = calculate_similarity(frame, prev_frame)
            if similarity < threshold:
                is_keyframe = True

        if is_keyframe:
            # Check max frames limit
            if max_frames is not None and extracted_count >= max_frames:
                break

            # Resize frame
            resized = cv2.resize(frame, (out_width, out_height), interpolation=cv2.INTER_AREA)

            # Convert BGR to RGB for PIL
            rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            # Save as JPEG with specified quality
            timestamp = frame_number / fps if fps > 0 else 0
            filename = f"frame_{extracted_count + 1:03d}.jpg"
            filepath = os.path.join(output_dir, filename)

            img.save(filepath, "JPEG", quality=quality, optimize=True)

            file_size = os.path.getsize(filepath)
            total_size += file_size

            keyframes.append({
                "filename": filename,
                "frame_number": frame_number,
                "timestamp": timestamp,
                "file_size": file_size
            })

            extracted_count += 1
            print(f"  Extracted: {filename} (frame {frame_number}, {timestamp:.2f}s, {file_size / 1024:.1f}KB)")

        prev_frame = frame.copy()
        frame_number += 1

    cap.release()

    # Calculate statistics
    total_size_mb = total_size / (1024 * 1024)
    estimated_tokens = int(total_size / 50)  # Rough estimate: ~50 bytes per token for images
    haiku_cost = (estimated_tokens / 1_000_000) * 0.25  # Haiku input cost

    stats = {
        "video_path": video_path,
        "output_dir": output_dir,
        "video_duration": duration,
        "video_fps": fps,
        "original_size": f"{width}x{height}",
        "output_size": f"{out_width}x{out_height}",
        "total_video_frames": total_frames,
        "extracted_keyframes": extracted_count,
        "total_size_bytes": total_size,
        "total_size_mb": total_size_mb,
        "estimated_tokens": estimated_tokens,
        "estimated_haiku_cost_usd": haiku_cost,
        "estimated_haiku_cost_jpy": haiku_cost * 150,  # Approximate JPY
        "keyframes": keyframes,
        "settings": {
            "threshold": threshold,
            "quality": quality,
            "scale": scale
        }
    }

    return stats


def print_summary(stats: dict) -> None:
    """Print extraction summary."""
    print()
    print("=" * 60)
    print("Extraction Summary")
    print("=" * 60)
    print(f"Video: {stats['video_path']}")
    print(f"Duration: {stats['video_duration']:.2f}s")
    print(f"Total frames in video: {stats['total_video_frames']}")
    print(f"Keyframes extracted: {stats['extracted_keyframes']}")
    print(f"Output directory: {stats['output_dir']}")
    print(f"Output size: {stats['output_size']}")
    print(f"Total size: {stats['total_size_mb']:.2f}MB")
    print(f"Estimated tokens: ~{stats['estimated_tokens']:,}")
    print(f"Estimated cost (Haiku): ${stats['estimated_haiku_cost_usd']:.4f} (~{stats['estimated_haiku_cost_jpy']:.1f}円)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Extract keyframes from a video file for Claude Code analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python extract_keyframes.py video.mp4

  # Custom output directory
  python extract_keyframes.py video.mp4 -o /tmp/my_keyframes/

  # Higher quality extraction
  python extract_keyframes.py video.mp4 -t 0.9 -q 50 -s 0.5

  # Limit to 20 keyframes
  python extract_keyframes.py video.mp4 -m 20
"""
    )

    parser.add_argument("video", help="Path to the input video file")
    parser.add_argument(
        "-o", "--output",
        help="Output directory (default: ./keyframes/<video_name>_<timestamp>/)"
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (0.0-1.0, default: 0.85)"
    )
    parser.add_argument(
        "-q", "--quality",
        type=int,
        default=30,
        help="JPEG quality (1-100, default: 30)"
    )
    parser.add_argument(
        "-s", "--scale",
        type=float,
        default=0.3,
        help="Scale factor (0.1-1.0, default: 0.3)"
    )
    parser.add_argument(
        "-m", "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to extract (default: unlimited)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not 0.0 <= args.threshold <= 1.0:
        parser.error("Threshold must be between 0.0 and 1.0")
    if not 1 <= args.quality <= 100:
        parser.error("Quality must be between 1 and 100")
    if not 0.1 <= args.scale <= 1.0:
        parser.error("Scale must be between 0.1 and 1.0")
    if args.max_frames is not None and args.max_frames < 1:
        parser.error("Max frames must be at least 1")

    # Generate default output directory
    if args.output is None:
        video_name = Path(args.video).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"./keyframes/{video_name}_{timestamp}"

    try:
        stats = extract_keyframes(
            video_path=args.video,
            output_dir=args.output,
            threshold=args.threshold,
            quality=args.quality,
            scale=args.scale,
            max_frames=args.max_frames
        )
        print_summary(stats)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

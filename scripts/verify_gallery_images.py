#!/usr/bin/env python3
"""Verify gallery images for the PG-EAM homepage carousel.

Checks resolution, aspect ratio, and file size of images in static/images/gallery/.
Generates a report with warnings for images that may not display optimally.
"""

import os
import struct
import sys
from pathlib import Path

GALLERY_DIR = Path(__file__).parent.parent / "static" / "images" / "gallery"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MIN_WIDTH = 800
RECOMMENDED_RATIO_MIN = 1.3  # Minimum aspect ratio (width/height) for landscape
MAX_FILE_SIZE_MB = 2


def get_png_dimensions(filepath):
    with open(filepath, "rb") as f:
        f.read(8)  # PNG signature
        f.read(4)  # chunk length
        f.read(4)  # chunk type (IHDR)
        width = struct.unpack(">I", f.read(4))[0]
        height = struct.unpack(">I", f.read(4))[0]
    return width, height


def get_jpeg_dimensions(filepath):
    with open(filepath, "rb") as f:
        f.read(2)  # SOI marker
        while True:
            marker = f.read(2)
            if len(marker) < 2:
                return None, None
            if marker[0] != 0xFF:
                return None, None
            if marker[1] in (0xC0, 0xC1, 0xC2):
                f.read(3)  # length + precision
                height = struct.unpack(">H", f.read(2))[0]
                width = struct.unpack(">H", f.read(2))[0]
                return width, height
            else:
                length = struct.unpack(">H", f.read(2))[0]
                f.read(length - 2)
    return None, None


def get_image_dimensions(filepath):
    ext = filepath.suffix.lower()
    if ext == ".png":
        return get_png_dimensions(filepath)
    elif ext in (".jpg", ".jpeg"):
        return get_jpeg_dimensions(filepath)
    return None, None


def main():
    if not GALLERY_DIR.exists():
        print(f"ERROR: Gallery directory not found: {GALLERY_DIR}")
        sys.exit(1)

    images = sorted(
        f for f in GALLERY_DIR.iterdir()
        if f.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if not images:
        print(f"WARNING: No images found in {GALLERY_DIR}")
        sys.exit(1)

    print("=" * 70)
    print("PG-EAM Gallery Image Verification Report")
    print("=" * 70)
    print(f"\nDirectory: {GALLERY_DIR}")
    print(f"Images found: {len(images)}\n")

    warnings = []

    for img in images:
        size_bytes = img.stat().st_size
        size_kb = size_bytes / 1024
        size_mb = size_kb / 1024
        width, height = get_image_dimensions(img)

        print(f"  {img.name}")

        if width and height:
            ratio = width / height
            orientation = "landscape" if ratio > 1.1 else ("portrait" if ratio < 0.9 else "square")
            print(f"    Dimensions: {width}x{height} ({orientation}, ratio {ratio:.2f})")
        else:
            print(f"    Dimensions: could not determine")
            warnings.append(f"  {img.name}: Could not read dimensions")

        print(f"    Size: {size_kb:.0f}KB ({size_mb:.2f}MB)")

        # Check warnings
        if width and width < MIN_WIDTH:
            w = f"  {img.name}: Width {width}px < recommended {MIN_WIDTH}px (may look blurry in carousel)"
            warnings.append(w)

        if width and height and (width / height) < RECOMMENDED_RATIO_MIN:
            w = f"  {img.name}: Aspect ratio {ratio:.2f} is not landscape (carousel uses object-cover, image will be cropped)"
            warnings.append(w)

        if size_mb > MAX_FILE_SIZE_MB:
            w = f"  {img.name}: File size {size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB (consider compressing)"
            warnings.append(w)

        print()

    if warnings:
        print("-" * 70)
        print(f"WARNINGS ({len(warnings)}):")
        print("-" * 70)
        for w in warnings:
            print(f"  ⚠ {w}")
        print()
        print("Note: Portrait and low-resolution images will still work in the carousel")
        print("but may be cropped or appear slightly blurry. For best results, use")
        print(f"landscape images with width >= {MIN_WIDTH}px.")
    else:
        print("All images pass quality checks!")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()

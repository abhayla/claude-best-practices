#!/usr/bin/env python3
"""
Auto-resize screenshots to prevent Claude API 400 errors.

The Claude API rejects images exceeding 2000px in either dimension during
multi-image conversations. This script resizes images to stay within a safe
1800px limit (buffer below the 2000px hard cap).

Usage:
    python .claude/hooks/resize_screenshot.py <file_path>    # Resize single file
    python .claude/hooks/resize_screenshot.py --all          # Resize all in screenshots dir
    python .claude/hooks/resize_screenshot.py --recent       # Resize files modified in last 10s
"""

import os
import sys
import time

MAX_DIM = 1800
SCREENSHOTS_DIR = "docs/testing/screenshots"


def strip_adb_warnings(path):
    """Strip ADB warning text prepended to PNG data.

    When multiple displays exist, `adb exec-out screencap -p` prepends
    warning text like '[Warning] Multiple displays were found...' before
    the actual PNG binary. This corrupts the file. Fix by finding the
    PNG magic bytes (\\x89PNG) and stripping everything before them.

    Also detects screencap failures (e.g., 'Display Id not valid') where
    the file contains only error text with no PNG data at all.
    """
    try:
        with open(path, "rb") as f:
            data = f.read(512)  # Read header to check
        png_magic = b"\x89PNG"
        if data.startswith(png_magic):
            return False  # Already valid PNG

        # Check for screencap failure (error text only, no PNG data)
        if len(data) < 1000 and png_magic not in data:
            try:
                text = data.decode("utf-8", errors="replace").strip()
                if any(k in text for k in ("Failed to take", "Display Id", "Capturing failed")):
                    print(f"SCREENCAP_FAILED: {text}", file=sys.stderr)
                    return False
            except Exception:
                pass

        idx = data.find(png_magic)
        if idx <= 0:
            return False  # Not a PNG at all, skip
        # Re-read full file and strip prefix
        with open(path, "rb") as f:
            full_data = f.read()
        idx = full_data.find(png_magic)
        with open(path, "wb") as f:
            f.write(full_data[idx:])
        return True
    except Exception:
        return False


def resize_if_needed(path):
    """Resize image at path if either dimension exceeds MAX_DIM.

    Also repairs files corrupted by ADB warning text prepended to PNG data.
    """
    # Ensure parent directory exists
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    # First, fix ADB warning corruption if present
    was_stripped = strip_adb_warnings(path)

    # Verify the file starts with PNG magic after stripping
    if was_stripped:
        try:
            with open(path, "rb") as f:
                header = f.read(4)
            if header != b"\x89PNG":
                print(f"WARNING: {path} still not valid PNG after stripping", file=sys.stderr)
                return False
        except Exception:
            return False

    try:
        from PIL import Image
    except ImportError:
        # PIL not available — skip resize but file may still be valid
        return False

    try:
        img = Image.open(path)
        w, h = img.size
        if w <= MAX_DIM and h <= MAX_DIM:
            return False
        scale = min(MAX_DIM / w, MAX_DIM / h)
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.LANCZOS)
        img.save(path)
        return True
    except Exception as e:
        print(f"WARNING: Could not resize {path}: {e}", file=sys.stderr)
        return False


def process_directory(recent_only=False):
    """Resize all (or recently modified) screenshots in the directory."""
    if not os.path.isdir(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        return  # Just created, nothing to process
    now = time.time()
    for fname in os.listdir(SCREENSHOTS_DIR):
        fpath = os.path.join(SCREENSHOTS_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        if recent_only and (now - os.path.getmtime(fpath)) > 10:
            continue
        resize_if_needed(fpath)


def main():
    if len(sys.argv) < 2:
        print("Usage: resize_screenshot.py <file_path> | --all | --recent")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all":
        process_directory(recent_only=False)
    elif arg == "--recent":
        process_directory(recent_only=True)
    else:
        if os.path.isfile(arg):
            resize_if_needed(arg)


if __name__ == "__main__":
    main()

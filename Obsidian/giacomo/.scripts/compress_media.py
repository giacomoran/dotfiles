#!/usr/bin/env python3
"""Compress images and videos in Zxtra/Assets/ and update all markdown references.

Images are converted to WebP (quality 85). Videos are re-encoded to H.265/HEVC
in MP4 using Apple VideoToolbox hardware acceleration. Files where the output
would be larger than the original are skipped, as are already-optimal files
(already WebP or already H.265). GIFs and SVGs are never touched.

Usage:
    uv run compress_media.py           # dry run — shows what would change
    uv run compress_media.py --apply   # compress and update markdown files
"""

import argparse
import io
import subprocess
from pathlib import Path

from PIL import Image

VAULT_PATH = Path(__file__).parent.parent
ASSETS_PATH = VAULT_PATH / "Zxtra" / "Assets"

# Image formats to convert to WebP. Everything else (gif, svg, webp, pdf…) is left alone.
CONVERTIBLE_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
# Video formats to re-encode to H.265. Already-H.265 files are skipped automatically.
CONVERTIBLE_VIDEO_SUFFIXES = {".mp4", ".mov"}

WEBP_QUALITY = 85
VIDEO_QUALITY = 65  # hevc_videotoolbox quality (0–100, higher is better quality)


# ── Image conversion ──────────────────────────────────────────────────────────

def encode_as_webp(src: Path) -> bytes:
    with Image.open(src) as img:
        # Preserve transparency for RGBA images; use RGB for everything else.
        mode = "RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB"
        converted = img.convert(mode)
        buffer = io.BytesIO()
        converted.save(buffer, format="WEBP", quality=WEBP_QUALITY, method=6)
        return buffer.getvalue()


# ── Video conversion ──────────────────────────────────────────────────────────

def get_video_codec(src: Path) -> str:
    """Return the codec name of the first video stream (e.g. 'h264', 'hevc')."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(src),
        ],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def encode_as_hevc(src: Path, dest: Path) -> None:
    """Re-encode src to dest using H.265/HEVC via Apple VideoToolbox."""
    subprocess.run(
        [
            "ffmpeg", "-i", str(src),
            "-c:v", "hevc_videotoolbox",
            "-q:v", str(VIDEO_QUALITY),
            "-tag:v", "hvc1",       # Apple compatibility tag
            "-c:a", "aac", "-b:a", "128k",
            "-y", str(dest),
        ],
        check=True,
        capture_output=True,
    )


# ── Markdown reference update ─────────────────────────────────────────────────

def find_md_files(vault_path: Path) -> list[Path]:
    return [
        p for p in vault_path.rglob("*.md")
        if ".obsidian" not in p.parts and ".scripts" not in p.parts
    ]


def replace_filename_in_md_files(
    md_files: list[Path],
    old_name: str,
    new_name: str,
    dry_run: bool,
) -> list[Path]:
    """Replace all occurrences of old_name with new_name in markdown files.
    Returns the list of files that were (or would be) changed.
    """
    changed = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        if old_name not in content:
            continue
        updated = content.replace(old_name, new_name)
        changed.append(md_file)
        if not dry_run:
            md_file.write_text(updated, encoding="utf-8")
    return changed


# ── Image processing ──────────────────────────────────────────────────────────

def process_images(
    candidates: list[Path],
    md_files: list[Path],
    dry_run: bool,
) -> tuple[int, int, int, int, list[tuple[str, str]]]:
    """Process image candidates. Returns (total_original, total_compressed, skipped_larger, converted, errors)."""
    total_original = 0
    total_compressed = 0
    skipped_larger = 0
    converted = 0
    errors: list[tuple[str, str]] = []

    for src in candidates:
        original_size = src.stat().st_size
        dest = src.with_suffix(".webp")

        if dest.exists():
            print(f"  skip  {src.name}  (destination {dest.name} already exists)")
            continue

        try:
            webp_bytes = encode_as_webp(src)
        except Exception as exc:
            errors.append((src.name, str(exc)))
            continue

        webp_size = len(webp_bytes)
        saving = original_size - webp_size
        saving_pct = saving / original_size * 100

        if webp_size >= original_size:
            skipped_larger += 1
            print(f"  skip  {src.name}  (WebP would be larger)")
            continue

        print(
            f"  {'[dry]' if dry_run else 'conv '}  {src.name}"
            f"  {original_size // 1024}KB → {webp_size // 1024}KB"
            f"  (-{saving_pct:.0f}%)"
        )

        if not dry_run:
            dest.write_bytes(webp_bytes)
            src.unlink()

        changed_md = replace_filename_in_md_files(md_files, src.name, dest.name, dry_run)
        for md_file in changed_md:
            print(f"         ↳ {md_file.relative_to(VAULT_PATH)}")

        total_original += original_size
        total_compressed += webp_size
        converted += 1

    return total_original, total_compressed, skipped_larger, converted, errors


# ── Video processing ──────────────────────────────────────────────────────────

def process_videos(
    candidates: list[Path],
    md_files: list[Path],
    dry_run: bool,
) -> tuple[int, int, int, int, int, list[tuple[str, str]]]:
    """Process video candidates. Returns (total_original, total_compressed, skipped_hevc, skipped_larger, converted, errors)."""
    total_original = 0
    total_compressed = 0
    skipped_hevc = 0
    skipped_larger = 0
    converted = 0
    errors: list[tuple[str, str]] = []

    for src in candidates:
        original_size = src.stat().st_size
        dest = src.with_suffix(".mp4")

        # A .mov would be renamed to .mp4 — skip if that target already exists.
        if dest != src and dest.exists():
            print(f"  skip  {src.name}  (destination {dest.name} already exists)")
            continue

        try:
            codec = get_video_codec(src)
        except Exception as exc:
            errors.append((src.name, f"ffprobe: {exc}"))
            continue

        if codec == "hevc":
            skipped_hevc += 1
            print(f"  skip  {src.name}  (already H.265)")
            continue

        if dry_run:
            print(
                f"  [dry]  {src.name}"
                f"  {original_size // (1024 * 1024)}MB"
                f"  ({codec} → H.265)"
            )
            total_original += original_size
            converted += 1
            continue

        # Encode to a temp file so we can compare sizes before committing.
        temp_dest = src.parent / f"_tmp_{dest.name}"
        print(f"  encod  {src.name}  {original_size // (1024 * 1024)}MB  ({codec} → H.265) ...", end="", flush=True)
        try:
            encode_as_hevc(src, temp_dest)
        except Exception as exc:
            temp_dest.unlink(missing_ok=True)
            print(f"  error")
            errors.append((src.name, str(exc)))
            continue

        compressed_size = temp_dest.stat().st_size
        saving = original_size - compressed_size
        saving_pct = saving / original_size * 100

        if compressed_size >= original_size:
            skipped_larger += 1
            temp_dest.unlink()
            print(f"  skip (H.265 would be larger)")
            continue

        print(f"  → {compressed_size // (1024 * 1024)}MB  (-{saving_pct:.0f}%)")

        temp_dest.rename(dest)
        if dest != src:
            src.unlink()

        # Update markdown refs only when the filename changes (.mov → .mp4).
        if dest.name != src.name:
            changed_md = replace_filename_in_md_files(md_files, src.name, dest.name, dry_run=False)
            for md_file in changed_md:
                print(f"         ↳ {md_file.relative_to(VAULT_PATH)}")

        total_original += original_size
        total_compressed += compressed_size
        converted += 1

    return total_original, total_compressed, skipped_hevc, skipped_larger, converted, errors


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry run)")
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("Dry run — pass --apply to make changes.\n")

    image_candidates = sorted(
        p for p in ASSETS_PATH.iterdir()
        if p.suffix.lower() in CONVERTIBLE_IMAGE_SUFFIXES
    )
    video_candidates = sorted(
        p for p in ASSETS_PATH.iterdir()
        if p.suffix.lower() in CONVERTIBLE_VIDEO_SUFFIXES
    )

    if not image_candidates and not video_candidates:
        print("No compressible media found.")
        return

    md_files = find_md_files(VAULT_PATH)

    img_total_original = img_total_compressed = 0
    vid_total_original = vid_total_compressed = 0
    all_errors: list[tuple[str, str]] = []

    # -- Images
    if image_candidates:
        print(f"── Images ({len(image_candidates)}) " + "─" * 50)
        img_total_original, img_total_compressed, img_skipped_larger, img_converted, img_errors = process_images(
            image_candidates, md_files, dry_run
        )
        all_errors.extend(img_errors)

        img_saving = img_total_original - img_total_compressed
        img_pct = img_saving / img_total_original * 100 if img_total_original else 0
        action = "Would convert" if dry_run else "Converted"
        print(
            f"\n{action} {img_converted} image(s)"
            f"  |  {img_total_original / (1024 * 1024):.1f}MB → {img_total_compressed / (1024 * 1024):.1f}MB"
            f"  |  saving {img_saving / (1024 * 1024):.1f}MB ({img_pct:.0f}%)"
        )
        if img_skipped_larger:
            print(f"Skipped {img_skipped_larger} image(s) where WebP would be larger")

    # -- Videos
    if video_candidates:
        print(f"\n── Videos ({len(video_candidates)}) " + "─" * 50)
        vid_total_original, vid_total_compressed, vid_skipped_hevc, vid_skipped_larger, vid_converted, vid_errors = process_videos(
            video_candidates, md_files, dry_run
        )
        all_errors.extend(vid_errors)

        action = "Would encode" if dry_run else "Encoded"
        if dry_run:
            print(
                f"\n{action} {vid_converted} video(s)"
                f"  |  {vid_total_original / (1024 * 1024):.0f}MB total"
                f"  (savings unknown until encoded)"
            )
        if not dry_run:
            vid_saving = vid_total_original - vid_total_compressed
            vid_pct = vid_saving / vid_total_original * 100 if vid_total_original else 0
            print(
                f"\n{action} {vid_converted} video(s)"
                f"  |  {vid_total_original / (1024 * 1024):.0f}MB → {vid_total_compressed / (1024 * 1024):.0f}MB"
                f"  |  saving {vid_saving / (1024 * 1024):.0f}MB ({vid_pct:.0f}%)"
            )
        if vid_skipped_hevc:
            print(f"Skipped {vid_skipped_hevc} video(s) already encoded as H.265")
        if vid_skipped_larger:
            print(f"Skipped {vid_skipped_larger} video(s) where H.265 would be larger")

    # -- Errors
    if all_errors:
        print(f"\nErrors ({len(all_errors)}):")
        for name, msg in all_errors:
            print(f"  {name}: {msg}")

    if dry_run:
        print("\nRun with --apply to apply.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Batch crop SEM footers and redraw readable scale bars inside images."""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTS = {".tif", ".tiff", ".png", ".jpg", ".jpeg", ".bmp"}


def collect_images(paths: list[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTS:
            files.append(path)
        elif path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            files.extend(p for p in iterator if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    return sorted(dict.fromkeys(files))


def to_uint8_gray(image: Image.Image) -> np.ndarray:
    if image.mode in {"L", "P", "RGB", "RGBA"}:
        gray = image.convert("L")
        return np.asarray(gray, dtype=np.uint8)

    arr = np.asarray(image)
    if arr.ndim == 3:
        gray = image.convert("L")
        return np.asarray(gray, dtype=np.uint8)

    arr = arr.astype(np.float32)
    low = float(np.percentile(arr, 0.5))
    high = float(np.percentile(arr, 99.5))
    if high <= low:
        high = float(arr.max())
        low = float(arr.min())
    if high <= low:
        return np.zeros(arr.shape, dtype=np.uint8)
    arr = np.clip((arr - low) * 255.0 / (high - low), 0, 255)
    return arr.astype(np.uint8)


def to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image.copy()
    if image.mode in {"P", "RGBA"}:
        return image.convert("RGB")

    gray = to_uint8_gray(image)
    return Image.fromarray(gray, mode="L").convert("RGB")


def longest_true_run(row: np.ndarray) -> tuple[int, int]:
    best_start = 0
    best_len = 0
    current_start = 0
    current_len = 0
    for index, value in enumerate(row):
        if value:
            if current_len == 0:
                current_start = index
            current_len += 1
        elif current_len:
            if current_len > best_len:
                best_start = current_start
                best_len = current_len
            current_len = 0
    if current_len > best_len:
        best_start = current_start
        best_len = current_len
    return best_start, best_len


def detect_colored_source_scale_bar(rgb: Image.Image) -> tuple[int | None, int | None, int | None]:
    arr = np.asarray(rgb.convert("RGB"), dtype=np.uint8)
    height, width, _ = arr.shape
    r = arr[:, :, 0].astype(np.int16)
    g = arr[:, :, 1].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)

    # ZEISS exports commonly draw the source scale bar in bright green.
    colored = (g > 120) & (g - r > 45) & (g - b > 45)
    start_y = int(height * 0.55)
    end_y = int(height * 0.98)
    min_run = max(18, int(width * 0.025))
    max_run = int(width * 0.45)

    best: tuple[int | None, int | None, int | None] = (None, None, None)
    best_len = 0
    for y in range(start_y, end_y):
        x0, run_len = longest_true_run(colored[y])
        if min_run <= run_len <= max_run and run_len > best_len:
            best = (x0, y, run_len)
            best_len = run_len
    return best


def detect_bright_source_scale_bar(gray: np.ndarray) -> tuple[int | None, int | None, int | None]:
    height, width = gray.shape
    start_y = int(height * 0.52)
    threshold = max(210, int(np.percentile(gray, 99.2) * 0.82))
    bright = gray[start_y:] >= threshold
    min_run = max(22, int(width * 0.045))
    max_run = int(width * 0.72)

    best: tuple[int | None, int | None, int | None] = (None, None, None)
    best_len = 0
    for local_y, row in enumerate(bright):
        x0, run_len = longest_true_run(row)
        if min_run <= run_len <= max_run and run_len > best_len:
            best = (x0, start_y + local_y, run_len)
            best_len = run_len
    return best


def detect_source_scale_bar(
    gray: np.ndarray,
    rgb: Image.Image | None = None,
) -> tuple[int | None, int | None, int | None]:
    if rgb is not None:
        colored = detect_colored_source_scale_bar(rgb)
        if colored[2] is not None:
            return colored
    return detect_bright_source_scale_bar(gray)


def normalize_tag_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        for encoding in ("utf-8", "utf-16le", "latin-1"):
            try:
                return value.decode(encoding, errors="ignore").replace("\x00", "")
            except UnicodeDecodeError:
                continue
        return ""
    return str(value).replace("\x00", "")


def extract_pixel_size_m(image: Image.Image) -> float | None:
    tag_source = getattr(image, "tag_v2", {})
    for tag_id in (34118, 34119):
        text = normalize_tag_text(tag_source.get(tag_id))
        if not text:
            continue
        for line in text.splitlines():
            stripped = line.strip()
            if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", stripped):
                continue
            try:
                value = float(stripped)
            except ValueError:
                continue
            if 1e-12 <= value <= 1e-4:
                return value
    return None


def format_scale_label(value: float, unit: str) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-6:
        text = str(int(rounded))
    else:
        text = f"{value:.3g}"
    return f"{text} {unit}"


def infer_scale_label(bar_length_px: int | None, pixel_size_m: float | None) -> str | None:
    if bar_length_px is None or pixel_size_m is None:
        return None

    length_um = float(bar_length_px) * pixel_size_m * 1_000_000.0
    if length_um <= 0:
        return None

    if length_um >= 1.0:
        unit = "µm"
        unit_value = length_um
    else:
        unit = "nm"
        unit_value = length_um * 1000.0

    exponent = math.floor(math.log10(unit_value))
    candidates = []
    for power in range(exponent - 1, exponent + 2):
        for base in (1.0, 2.0, 5.0):
            candidates.append(base * (10.0**power))
    best = min(candidates, key=lambda item: abs(math.log(item / unit_value)))
    relative_error = abs(best - unit_value) / unit_value
    if relative_error > 0.30:
        return format_scale_label(unit_value, unit)
    return format_scale_label(best, unit)


def smooth(values: np.ndarray, window: int) -> np.ndarray:
    window = max(3, window | 1)
    kernel = np.ones(window, dtype=np.float32) / float(window)
    return np.convolve(values, kernel, mode="same")


def detect_footer_top(gray: np.ndarray, crop_ratio: float | None, crop_px: int | None) -> int:
    height, width = gray.shape
    if crop_px is not None:
        return max(1, min(height, height - crop_px))
    if crop_ratio is not None:
        return max(1, min(height, int(round(height * (1.0 - crop_ratio)))))

    lo = int(height * 0.58)
    hi = int(height * 0.95)
    if hi <= lo + 8:
        return int(height * 0.84)

    means = gray.mean(axis=1)
    stds = gray.std(axis=1)
    bright_frac = (gray > 220).mean(axis=1) * 255.0

    win = max(5, height // 120)
    means = smooth(means, win)
    stds = smooth(stds, win)
    bright_frac = smooth(bright_frac, win)

    scores: list[tuple[float, int]] = []
    band_min = int(height * 0.08)
    band_max = int(height * 0.35)
    sample = max(4, height // 160)
    threshold = max(210, int(np.percentile(gray, 99.2) * 0.82))
    long_runs = np.zeros(height, dtype=np.float32)
    for row_index in range(lo, hi):
        _, run_len = longest_true_run(gray[row_index] >= threshold)
        long_runs[row_index] = run_len / float(width)

    for y in range(lo, hi):
        top_slice = slice(max(0, y - sample), y)
        bottom_slice = slice(y, min(height, y + sample))
        if top_slice.stop <= top_slice.start or bottom_slice.stop <= bottom_slice.start:
            continue

        mean_delta = abs(float(means[top_slice].mean() - means[bottom_slice].mean()))
        std_delta = abs(float(stds[top_slice].mean() - stds[bottom_slice].mean()))
        bright_delta = abs(float(bright_frac[top_slice].mean() - bright_frac[bottom_slice].mean()))
        footer_h = height - y
        footer_ratio = footer_h / float(height)
        centered_preference = math.exp(-((footer_ratio - 0.17) / 0.10) ** 2)
        band_preference = 1.0 if band_min <= footer_h <= band_max else 0.45
        nearby_run = float(long_runs[max(0, y - 4) : min(height, y + 5)].max())
        scale_line_penalty = 0.28 if nearby_run > 0.045 else 1.0
        score = (
            mean_delta + 0.70 * std_delta + 0.16 * bright_delta
        ) * max(0.25, centered_preference) * band_preference * scale_line_penalty
        scores.append((score, y))

    if not scores:
        return int(height * 0.84)

    best_score, best_y = max(scores, key=lambda item: item[0])
    if best_score < 7.5:
        return int(height * 0.84)
    return best_y


def find_arial_font() -> str | None:
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/Arial.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = find_arial_font()
    if font_path:
        return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_font_to_bar_length(
    draw: ImageDraw.ImageDraw,
    label: str,
    bar_len: int,
    explicit_font_size: int | None,
) -> tuple[ImageFont.ImageFont, int, int, int]:
    if explicit_font_size is not None:
        size = max(6, min(explicit_font_size, 96))
        font = load_font(size)
        label_w, label_h = text_size(draw, label, font)
        return font, size, label_w, label_h

    best: tuple[int, ImageFont.ImageFont, int, int, int] | None = None
    for size in range(6, 97):
        font = load_font(size)
        label_w, label_h = text_size(draw, label, font)
        difference = abs(label_w - bar_len)
        if best is None or difference < best[0] or (
            difference == best[0] and label_w <= bar_len < best[3]
        ):
            best = (difference, font, size, label_w, label_h)

    if best is None:
        font = load_font(12)
        label_w, label_h = text_size(draw, label, font)
        return font, 12, label_w, label_h

    _, font, size, label_w, label_h = best
    return font, size, label_w, label_h


def draw_scale_bar(
    image: Image.Image,
    label: str,
    bar_length_px: int | None,
    font_size: int | None,
    position: str,
) -> tuple[Image.Image, dict[str, int]]:
    output = image.copy().convert("RGB")
    width, height = output.size
    draw = ImageDraw.Draw(output)

    bar_thickness = max(4, int(round(width * 0.010)))
    margin_x = max(12, int(round(width * 0.030)))
    margin_y = max(12, int(round(height * 0.045)))
    gap = max(5, int(round(height * 0.018)))

    if bar_length_px is None:
        raise ValueError("No source scale-bar length was detected. Provide --bar-length-px.")
    bar_len = max(1, int(round(bar_length_px)))
    max_bar_len = max(1, width - (2 * margin_x))
    if bar_len > max_bar_len:
        bar_len = max_bar_len

    font, size, label_w, label_h = fit_font_to_bar_length(draw, label, bar_len, font_size)

    if position == "lower-right":
        bar_x0 = width - margin_x - bar_len
        label_x = min(width - margin_x - label_w, bar_x0)
    else:
        bar_x0 = margin_x
        label_x = margin_x

    bar_y0 = height - margin_y - bar_thickness
    label_y = max(0, bar_y0 - gap - label_h)
    bar_y1 = bar_y0 + bar_thickness
    bar_x1 = bar_x0 + bar_len - 1

    shadow = max(1, bar_thickness // 3)
    shadow_color = (0, 0, 0)
    white = (255, 255, 255)

    draw.text((label_x + shadow, label_y + shadow), label, fill=shadow_color, font=font)
    draw.text((label_x, label_y), label, fill=white, font=font)
    draw.rectangle(
        [bar_x0 + shadow, bar_y0 + shadow, bar_x1 + shadow, bar_y1 + shadow],
        fill=shadow_color,
    )
    draw.rectangle([bar_x0, bar_y0, bar_x1, bar_y1], fill=white)
    return output, {
        "drawn_bar_px": bar_len,
        "font_size_px": size,
        "label_width_px": label_w,
        "label_height_px": label_h,
    }


def unique_output_path(out_dir: Path, stem: str, suffix: str, ext: str) -> Path:
    candidate = out_dir / f"{stem}{suffix}.{ext}"
    if not candidate.exists():
        return candidate
    for index in range(2, 10000):
        candidate = out_dir / f"{stem}{suffix}-{index}.{ext}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to create unique output path for {stem}")


def process_one(path: Path, args: argparse.Namespace, out_dir: Path) -> dict[str, str | int]:
    with Image.open(path) as image:
        rgb = to_rgb(image)
        gray = to_uint8_gray(image)
        scale_x, scale_y, detected_bar_len = detect_source_scale_bar(gray, rgb)
        pixel_size_m = extract_pixel_size_m(image)
        inferred_label = infer_scale_label(detected_bar_len, pixel_size_m)
        crop_top_y = detect_footer_top(gray, args.crop_bottom_ratio, args.crop_bottom_px)
        cropped = rgb.crop((0, 0, rgb.size[0], crop_top_y))

    bar_len = args.bar_length_px or detected_bar_len
    scale_label = args.scale_label or inferred_label
    if bar_len is None:
        raise ValueError("Could not detect the original scale-bar length; provide --bar-length-px.")
    if not scale_label:
        raise ValueError("Could not infer the original scale label; provide --scale-label.")

    processed, scale_metrics = draw_scale_bar(
        cropped,
        label=scale_label,
        bar_length_px=bar_len,
        font_size=args.font_size,
        position=args.position,
    )

    out_path = unique_output_path(out_dir, path.stem, args.suffix, args.format.lower())
    save_kwargs = {}
    if args.format.lower() in {"jpg", "jpeg"}:
        save_kwargs["quality"] = 95
    processed.save(out_path, **save_kwargs)

    return {
        "source_file": str(path),
        "output_file": str(out_path),
        "original_width": rgb.size[0],
        "original_height": rgb.size[1],
        "output_width": processed.size[0],
        "output_height": processed.size[1],
        "cropped_bottom_px": rgb.size[1] - crop_top_y,
        "detected_source_scale_x": "" if scale_x is None else scale_x,
        "detected_source_scale_y": "" if scale_y is None else scale_y,
        "scale_bar_px": "" if bar_len is None else int(bar_len),
        "scale_label": scale_label,
        "source_pixel_size_m": "" if pixel_size_m is None else f"{pixel_size_m:.9g}",
        "inferred_scale_label": "" if inferred_label is None else inferred_label,
        "drawn_bar_px": scale_metrics["drawn_bar_px"],
        "font_size_px": scale_metrics["font_size_px"],
        "label_width_px": scale_metrics["label_width_px"],
        "label_height_px": scale_metrics["label_height_px"],
    }


def make_contact_sheet(image_paths: list[Path], out_path: Path) -> None:
    if not image_paths:
        return

    thumbs: list[Image.Image] = []
    thumb_w = 360
    thumb_h = 260
    resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
    for path in image_paths:
        with Image.open(path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h), resample)
            canvas = Image.new("RGB", (thumb_w, thumb_h), (245, 245, 245))
            x = (thumb_w - thumb.size[0]) // 2
            y = (thumb_h - thumb.size[1]) // 2
            canvas.paste(thumb, (x, y))
            thumbs.append(canvas)

    cols = min(4, len(thumbs))
    rows = int(math.ceil(len(thumbs) / cols))
    sheet = Image.new("RGB", (cols * thumb_w, rows * thumb_h), (255, 255, 255))
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * thumb_w
        y = (idx // cols) * thumb_h
        sheet.paste(thumb, (x, y))
    sheet.save(out_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crop SEM footer areas and redraw Arial scale bars inside images.",
    )
    parser.add_argument("inputs", nargs="+", help="SEM image files or folders.")
    parser.add_argument("--output-dir", help="Folder for processed images.")
    parser.add_argument("--recursive", action="store_true", help="Process subfolders.")
    parser.add_argument(
        "--scale-label",
        help="Scale label text. If omitted, infer it from the source scale bar and metadata.",
    )
    parser.add_argument("--crop-bottom-px", type=int, help="Exact bottom pixels to crop.")
    parser.add_argument("--crop-bottom-ratio", type=float, help="Bottom ratio to crop.")
    parser.add_argument("--bar-length-px", type=int, help="Redrawn scale-bar length in pixels.")
    parser.add_argument("--font-size", type=int, help="Arial label font size.")
    parser.add_argument(
        "--position",
        choices=["lower-left", "lower-right"],
        default="lower-left",
        help="Scale-bar position inside the image.",
    )
    parser.add_argument("--suffix", default="_scale_in_image", help="Output filename suffix.")
    parser.add_argument("--format", default="png", choices=["png", "jpg", "jpeg", "tif", "tiff"])
    parser.add_argument("--no-contact-sheet", action="store_true", help="Skip contact sheet.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    images = collect_images(args.inputs, args.recursive)
    if not images:
        print("No supported SEM image files found.", file=sys.stderr)
        return 2

    if args.output_dir:
        out_dir = Path(args.output_dir).expanduser()
    else:
        first = images[0]
        base = first.parent if first.is_file() else Path.cwd()
        out_dir = base / "processed_sem_scale_bar"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    output_paths: list[Path] = []
    for image_path in images:
        try:
            row = process_one(image_path, args, out_dir)
            rows.append(row)
            output_paths.append(Path(str(row["output_file"])))
            print(f"Processed: {image_path} -> {row['output_file']}")
        except Exception as exc:  # noqa: BLE001 - batch mode should continue.
            rows.append({"source_file": str(image_path), "output_file": "", "error": str(exc)})
            print(f"Failed: {image_path}: {exc}", file=sys.stderr)

    summary_path = out_dir / "processing_summary.csv"
    fieldnames = [
        "source_file",
        "output_file",
        "original_width",
        "original_height",
        "output_width",
        "output_height",
        "cropped_bottom_px",
        "detected_source_scale_x",
        "detected_source_scale_y",
        "scale_bar_px",
        "scale_label",
        "source_pixel_size_m",
        "inferred_scale_label",
        "drawn_bar_px",
        "font_size_px",
        "label_width_px",
        "label_height_px",
        "error",
    ]
    with summary_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})

    if output_paths and not args.no_contact_sheet:
        make_contact_sheet(output_paths, out_dir / "contact_sheet.png")

    succeeded = sum(1 for row in rows if row.get("output_file"))
    print(f"Done. Processed {succeeded}/{len(images)} images.")
    print(f"Output folder: {out_dir}")
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())

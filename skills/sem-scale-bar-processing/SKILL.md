---
name: sem-scale-bar-processing
description: Automatically use this skill when the user asks Codex to modify SEM images, process SEM/TIF microscopy images, redraw or move scale bars/标度尺, remove the bottom invalid annotation area, delete stray vertical white scale-marker lines, or batch export cleaned SEM figures. It provides an autonomous script for Arial scale-bar rendering and dedicated output folders.
---

# SEM Scale Bar Processing

## Overview

Use this skill to batch-clean SEM images whose original export contains a bottom annotation/status area. The standard result is a cropped SEM image with the scale bar redrawn inside the image area, matching the user's preferred style.

Before processing, load `references/default_prompt_zh.md` unless the current request explicitly changes a requirement.

## Default Style

- Create a new dedicated output folder; never overwrite the original SEM files.
- Remove the bottom invalid content/annotation area.
- Redraw the scale bar inside the image, normally in the lower-left corner.
- Preserve the original scale bar: use the source image's detected scale-bar pixel length and the source label or metadata-inferred label. Do not resize the bar from image width or use an arbitrary default label when the original can be detected.
- Use Arial for the scale label.
- Size the label text smaller and fit it to the scale bar: by default, the whole label text width should match the horizontal scale-bar length as closely as possible.
- Use white text and a white horizontal scale bar.
- Draw only the horizontal scale bar; do not draw right-side or left-side thin vertical marker lines.
- If the original scale cannot be inferred from the image or metadata, require explicit `--scale-label` and `--bar-length-px` values instead of silently inventing a scale.
- Prefer PNG output for clean sharing; preserve the source stem in filenames.
- Generate a contact sheet for visual QA when processing multiple images.

## Workflow

1. Identify SEM image inputs. Accept `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`, and `.bmp`; if a directory is supplied, batch process matching files.
2. Use `scripts/process_sem_scale_bar.py` for autonomous processing.
3. Let the script estimate the footer crop, original scale-bar length, and original scale label. For ZEISS TIFF exports, prefer the green scale-bar pixels plus metadata-derived calibration. Override with options only when the user gives exact crop/scale values or the automatic output is visibly wrong.
4. Save outputs to a folder named `processed_sem_scale_bar` unless the user asks for a different folder.
5. Verify representative outputs or the generated `contact_sheet.png` before saying the task is complete.

## Script

Run the bundled script directly:

```powershell
python path\to\sem-scale-bar-processing\scripts\process_sem_scale_bar.py `
  --output-dir "processed_sem_scale_bar" `
  "E:\path\to\sem-images"
```

Useful options:

- `--recursive`: process images in subfolders.
- `--scale-label`: manually set the displayed label, for example `1 µm`, `500 nm`, or `2 µm`. Leave omitted when the original label can be inferred.
- `--crop-bottom-px`: manually crop an exact number of pixels from the bottom.
- `--crop-bottom-ratio`: manually crop a bottom ratio, for example `0.16`.
- `--bar-length-px`: manually set the redrawn scale-bar pixel length; use this only when automatic source detection is wrong or unavailable.
- `--font-size`: manually set Arial label size. If omitted, the script automatically picks the size whose label width best matches the scale-bar length.
- `--format`: output format, default `png`.
- `--no-contact-sheet`: skip contact sheet generation.

## Continuous Improvement

Treat this skill as a living workflow for the user's SEM figure style.

- When the user gives a correction that should apply to future SEM images, update `references/default_prompt_zh.md`, this `SKILL.md`, or `scripts/process_sem_scale_bar.py`.
- Persist stable preferences such as font size, crop behavior, scale-bar position, scale label, output format, or folder naming.
- Do not persist one-off image-specific tweaks unless the user asks to make them the default.
- After modifying this skill, validate it with `quick_validate.py`, run the script on a small synthetic or real SEM sample, and publish it with `publish-skill-to-github`.

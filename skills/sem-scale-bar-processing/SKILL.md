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
- Use Arial for the scale label.
- Use a larger, reduced-view-readable font size.
- Use white text and a white horizontal scale bar.
- Draw only the horizontal scale bar; do not draw right-side or left-side thin vertical marker lines.
- Default scale label is `1μm` if the user does not specify another label.
- Prefer PNG output for clean sharing; preserve the source stem in filenames.
- Generate a contact sheet for visual QA when processing multiple images.

## Workflow

1. Identify SEM image inputs. Accept `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg`, and `.bmp`; if a directory is supplied, batch process matching files.
2. Use `scripts/process_sem_scale_bar.py` for autonomous processing.
3. Let the script estimate the footer crop and original scale-bar length. Override with options only when the user gives exact crop/scale values or the automatic output is visibly wrong.
4. Save outputs to a folder named `processed_sem_scale_bar` unless the user asks for a different folder.
5. Verify representative outputs or the generated `contact_sheet.png` before saying the task is complete.

## Script

Run the bundled script directly:

```powershell
python path\to\sem-scale-bar-processing\scripts\process_sem_scale_bar.py `
  --output-dir "processed_sem_scale_bar" `
  --scale-label "1μm" `
  "E:\path\to\sem-images"
```

Useful options:

- `--recursive`: process images in subfolders.
- `--scale-label`: set the displayed label, for example `1μm`, `500nm`, or `2μm`.
- `--crop-bottom-px`: manually crop an exact number of pixels from the bottom.
- `--crop-bottom-ratio`: manually crop a bottom ratio, for example `0.16`.
- `--bar-length-px`: manually set the redrawn scale-bar pixel length.
- `--font-size`: manually set Arial label size.
- `--format`: output format, default `png`.
- `--no-contact-sheet`: skip contact sheet generation.

## Continuous Improvement

Treat this skill as a living workflow for the user's SEM figure style.

- When the user gives a correction that should apply to future SEM images, update `references/default_prompt_zh.md`, this `SKILL.md`, or `scripts/process_sem_scale_bar.py`.
- Persist stable preferences such as font size, crop behavior, scale-bar position, scale label, output format, or folder naming.
- Do not persist one-off image-specific tweaks unless the user asks to make them the default.
- After modifying this skill, validate it with `quick_validate.py`, run the script on a small synthetic or real SEM sample, and publish it with `publish-skill-to-github`.

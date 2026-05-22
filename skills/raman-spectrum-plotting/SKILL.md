---
name: raman-spectrum-plotting
description: Automatically use this skill whenever the user asks Codex to plot, draw, process, generate, or batch create Raman spectra/拉曼光谱/Raman images from .txt, .csv, or two-column data files. Create publication-style Raman spectrum plots with fixed Raman shift ranges such as 0-1600 or 0-2000 cm^-1, thick dark curves, detected peak-position labels, emphasized carbon D/G peaks as C-D and C-G, PNG/SVG outputs, contact sheets, and peak-position tables.
---

# Raman Spectrum Plotting

## Overview

Use this skill to turn Raman `.txt` data into consistent publication-style figures. The expected input is a two-column text file: Raman shift in the first column and intensity in the second column.

This skill is the standing workflow for this user's Raman plotting tasks. If the user asks to draw Raman figures from data, process Raman spectra, make Raman images, or "use the same Raman plotting requirements", apply this skill without asking for confirmation unless an input file or x-axis range is ambiguous.

## Standing Prompt

Before plotting, load and follow the reusable Chinese prompt in `references/default_prompt_zh.md` unless the user's current request explicitly changes a requirement. The current user request has priority over the standing prompt; the standing prompt has priority over generic plotting defaults.

## Default Style

- Plot each input file separately unless the user explicitly asks for overlaid spectra.
- Save outputs in a new folder dedicated to processed Raman figures.
- Use a white background, black axes, inward ticks, and thick axis spines.
- Use Times New Roman styling for labels, ticks, legend, and peak numbers.
- Use bold axis labels:
  - `Raman Shift (cm^-1)` with superscript formatting in the figure.
  - `Raman Intensity (offset)`.
- Hide y-axis tick labels, but keep y-axis ticks.
- Use dark, thick curves:
  - Red samples: `#D00000`.
  - Blue samples: `#0047B3`.
  - Purple/origin samples: `#8A00CC`.
  - Preferred line width: `2.15`.
- Draw vertical black dotted guide lines for peaks.
- Label peak positions above the guide line in bold black text.
- Label carbon peaks specially:
  - D band: `C-D`, detected in the 1280-1450 cm^-1 window.
  - G band: `C-G`, detected in the 1500-min(1650, x_max) cm^-1 window.

## Workflow

1. Inspect input files and confirm they are numeric two-column spectra.
2. Create or reuse a dedicated output folder.
3. Restrict the plotted x-axis to the requested range:
   - If unspecified, use the user's most recent Raman preference.
   - Common ranges from this project: `0-1600` and `100-2000`.
4. Detect peaks using a smoothed, baseline-corrected trace, but plot the original intensity trace.
5. Always include C-D and C-G annotations when their windows fall inside the x-axis range.
6. Save each spectrum as both `.png` and `.svg`.
7. Save `peak_positions.csv` with columns:
   - `sample`
   - `source_file`
   - `peak_type`
   - `raman_shift_cm-1`
8. Generate a contact sheet for visual QA when processing multiple files.
9. Verify the output count, open the contact sheet or representative figures, and check that x-axis limits and labels match the request before responding.

## Script

Use `scripts/plot_raman.py` for repeatable batch plotting.

Example:

```powershell
python path\to\raman-spectrum-plotting\scripts\plot_raman.py `
  --out-dir "processed_raman_plots" `
  --x-min 0 `
  --x-max 1600 `
  "sample1.txt" "sample2.txt"
```

Useful options:

- `--x-min` and `--x-max`: set the displayed Raman shift range.
- `--out-dir`: output folder.
- `--line-width`: curve width; default is `2.15`.
- `--no-contact-sheet`: skip summary preview generation.

## Project-Specific Preferences

When working on this user's Raman data, default to:

- Separate figure for each `.txt` data file.
- Darkened, thick curve colors.
- Axis range `0-1600 cm^-1` if the user says "same as before" after the latest adjustment.
- Peak annotations within the visible x-axis range only.
- PNG and SVG outputs, plus `peak_positions.csv` and `contact_sheet.png`.

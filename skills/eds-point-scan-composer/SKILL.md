---
name: eds-point-scan-composer
description: Use this skill whenever the user explicitly says to use the EDS point-scan skill, EDS点扫图skill, EDS点扫描组图skill, or asks to compose, revise, compare, caption, summarize, or generate publication-style figures from EDS point-scan C percentage plots such as C_percent_plot_group images. Strongly trigger for Chinese prompts mentioning EDS 点扫, 点扫描, C元素含量, 碳百分比, 碳附着, 碳包覆效果, 原始样品/60甲烷20氢气/80甲烷 comparisons, or captions that must conclude carbon attachment/coating effect.
metadata:
  short-description: EDS point-scan C% group figures and conclusions
---

# EDS Point-Scan Composer

Use this skill to turn EDS point-scan C percentage plots into clean multi-panel figures, statistics, captions, and comparative conclusions about carbon attachment/coating effects.

If `scientific-figure-composer` is also active, follow its general figure rules, but let this skill's EDS point-scan rules take precedence.

## Before Starting

1. Read `references/user-preferences.md` and apply saved reusable preferences.
2. If the task is for the user's 2026-05-27 Si-C carbon-coating project, read `references/project-5-27-baselines.md` for known sample conditions and previously computed summary values.
3. Inspect all user-provided images and any experiment workbook before composing or writing conclusions.
4. Prefer original numeric data files when available. If only plot images are provided, extract values from visible point labels carefully and state that the statistics are based on the plotted labels.

## Continuous Improvement

When the user corrects the output, apply the correction immediately. Then decide whether it is reusable:

- Reusable: panel order, label placement, no-table rule, output naming, statistic fields, caption wording, comparison logic, or scientific interpretation limits.
- Task-only: a one-off figure number, one temporary sample name, or a special order for a single figure.

Append reusable corrections to `references/user-preferences.md` after finishing the task. If a correction becomes stable across several tasks, promote it into this `SKILL.md`.

## Inputs To Gather

- EDS point-scan plot images, usually PNG/TIF files named like `C_percent_plot_group_*.png`.
- Sample condition and treatment parameters, often from the experiment workbook.
- Figure number and sample grouping if implied by the current report or PPT.
- Whether the user wants only a figure, a caption, an analysis paragraph, or all deliverables.

## Default Figure Output

Create a new output folder under the relevant EDS point-scan or report folder:

`FigN_组图成品_YYYYMMDD_HHMMSS_<sample-condition>_EDS点扫描`

Include:

- final `.png`
- final `.tif` when useful for publication/report insertion
- `FigN_caption.txt`
- `FigN_analysis.txt` when a longer explanation is useful
- `processed_panels/` with normalized panel copies and source copies
- `summary_stats.csv` when numeric values were extracted or provided

## Layout Rules

- Use a clean white background and compact multi-panel layout.
- Preserve the plotted axes, point labels, and values.
- For EDS point-scan C% values grouped by sample position, default to boxplots: one sample per independent figure and one boxplot per measured position, with the five raw points overlaid.
- For small EDS point-scan groups, draw boxplot whiskers to the observed minimum and maximum values (Matplotlib `whis=(0, 100)`) so all measured points remain inside the plotted range rather than being visually separated as default 1.5 IQR outliers.
- Label each raw point with its C% value using a small, unobtrusive plain-text label with no box or border. For each boxplot, arrange the five labels in a neat single-side vertical column sorted from top to bottom by plotted value; keep labels readable but smaller than axis tick text and avoid covering the box, median line, or neighboring points.
- Use bold Arial panel labels `a`, `b`, `c`... placed immediately adjacent to the top-left of each panel.
- Do not add an in-figure statistics table unless the user explicitly asks for it.
- Put means, standard deviations, ranges, RSD, and conclusions in the caption or analysis text.
- If the user asks for separate single figures or "data-only" images, do not create a composite/group figure. Each image should contain only the plotted data, axes, tick labels, and numeric data labels; omit sample/region titles, panel letters, mean lines/text, parameter text, captions, and other in-figure annotations.
- Export at 600 dpi when possible and verify dimensions/DPI before final response.

## Statistic Rules

For each sample condition:

- `n`: number of EDS point measurements.
- Mean C content: arithmetic mean of C%.
- SD: sample standard deviation (`ddof=1`) when `n > 1`.
- Range: min-max C%.
- RSD: `SD / mean * 100%`.
- Differences: compare treated samples against the original baseline in percentage points.

Use cautious language because EDS C quantification is comparative: C is a light element and can be affected by surface topography, tilt, contamination, and interaction volume.

## Caption Pattern

Start every caption with `FigN |`.

Recommended structure:

1. Identify panel letters and sample condition.
2. State the treatment parameters when known: temperature, time, plasma power, gas set/actual flow, and pressure if relevant.
3. Report C% range, mean ± SD, and RSD.
4. Compare against original and other treatment conditions.
5. End with a concise conclusion about carbon attachment amount and coating uniformity.

## Interpretation Guide

Use these terms consistently:

- Original untreated sample: baseline C signal; extra PECVD carbon attachment/coating is limited.
- Moderate mean C increase with similar RSD to original: carbon attachment enhanced while uniformity remains relatively good.
- Very high mean C but high SD/RSD or separated high/low groups: strong carbon deposition/local carbon enrichment, but poorer coating uniformity and likely local thick carbon.

When comparing 60 sccm CH4/20 sccm H2 with 80 sccm CH4:

- 60CH4/20H2: emphasize moderate, more controlled carbon attachment and relatively uniform coating.
- 80CH4: emphasize strongest carbon signal and carbon attachment, but clear particle-to-particle variation and nonuniform/local thick coating risk.

## Workflow

1. Inspect file paths and source images.
2. Extract or load C% values for every panel.
3. Compute statistics and cross-condition differences.
4. Compose or revise the multi-panel figure according to layout rules.
5. Write caption and, if useful, an analysis file with:
   - 测试结果概述
   - 单个样品/颗粒分析
   - 不同参数对比
   - 结论与后续优化建议
6. Verify output folder contents, dimensions, DPI, and that labels are adjacent to panels.
7. Final response in Chinese: give the output folder, key files, verification evidence, and one-sentence scientific summary.

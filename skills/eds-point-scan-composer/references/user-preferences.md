# User Preferences for EDS Point-Scan Composer

This file stores reusable preferences learned from the user's EDS point-scan figure tasks. Update it after each task when the user gives a correction that should apply again.

## Figure Layout

- EDS point-scan group figures should not include an in-figure statistics table unless explicitly requested.
- For EDS point-scan C% values from Word/table data, automatically use boxplots by default: one sample per independent figure, one measured position per boxplot, and the five raw EDS points overlaid.
- Add small numeric C% labels next to every raw point in boxplots; for each boxplot, arrange labels in one neat side column ordered from top to bottom by plotted value. Labels should be plain text with no box or border, visible but unobtrusive, and should not dominate the figure.
- Put summary statistics and conclusions in `FigN_caption.txt` or `FigN_analysis.txt`.
- Use compact publication-style white-background layouts.
- Panel labels should be bold Arial letters placed immediately adjacent to the top-left of each panel, with no visible gap.
- When the user asks for EDS point-scan outputs as separate single figures, do not create a composite/group figure. Each image should contain only the data plot itself: no sample/region title, no panel letter, no mean annotation line/text, no parameter text, and no other extra in-figure labels beyond the plotted data, axes, tick labels, and numeric data labels.
- For EDS point-scan separate single figures, use generic x-axis tick labels `位置1` through `位置5` instead of spectrum numbers, and omit the x-axis title unless the user asks otherwise.
- When revising EDS point-scan C% figures for this project and the original spectrum numbers are not required, use generic x-axis tick labels `位置1` through `位置5` and set the x-axis title to `位置`.

## Statistics And Captions

- For 600 dpi EDS boxplots and EDS boxplot group figures, use physically readable font sizes and thick axes/box/median lines. Verify the composed group figure uses the newest bold source panels and that point-value labels remain visible without touching or crossing the axes.

- Focus interpretation on C element content, carbon attachment amount, and coating uniformity.
- Always compare treated samples with the original untreated baseline when those data are available.
- For treatment comparison, report mean ± SD, range, RSD, and percentage-point differences.
- Include the EDS light-element caveat in longer captions/analysis: C quantification is comparative and sensitive to morphology, tilt, and interaction volume.

## Project-Specific Defaults

- For this Si-C carbon-coating project, the common sample groups are:
  - Original untreated sample.
  - 60 sccm CH4 / 20 sccm H2 PECVD treatment.
  - 80 sccm CH4 PECVD treatment.
- The preferred conclusion style is direct but cautious: describe whether carbon attachment increased and whether coating appears uniform or locally enriched.

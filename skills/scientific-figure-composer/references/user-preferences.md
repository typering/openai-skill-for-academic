# User Preferences for Scientific Figure Composer

This file records reusable preferences learned from the user's scientific figure-making tasks. Update it after figure tasks when the user gives a new reusable correction or style preference.

## Output Organization

- Each completed figure task should create a new folder under the report/work folder.
- Save final `.png`, final `.tif` when requested or useful for publication, `FigN_caption.txt`, and `processed_panels/`.
- When analysis text is requested, save it as `.txt`; also create `.docx` when a standalone polished document is useful.

## Figure Style

- Use compact, publication-style layouts with minimal whitespace between related panels.
- Use a white background.
- For 600 dpi scientific group figures, use source-panel fonts and line widths large enough to remain readable after multi-panel composition; verify text readability in the final composed image, not only in the individual source panels.
- For similar percentage scatter plots, prefer moderately sized axis-title labels and larger numeric point-value labels.
- Use bold Arial panel labels `a`, `b`, `c`... placed immediately adjacent to the top-left of each panel; avoid visible gaps between the label and its image.
- Increase panel-label font size when labels look small.
- For microscopy multi-panel figures, place panel labels outside each image at the image's upper-left corner when possible, using large bold black Arial labels that remain readable after manuscript scaling.
- For SEM multi-panel figures when the user references a horizontal example layout, use a no-title horizontal grid, keep only panel labels inside the figure area, and put experimental conditions in captions or condition files.
- For SEM multi-panel revisions that reference a two-row example layout, use a compact two-row horizontal grid; keep only larger readable panel letters and original scale bars in the figure, place panel letters in the white margin to the left side of each image rather than above it, leave only a tight but visible horizontal gap between the label and image edge, keep labels outside the image area, do not increase image-to-image spacing when enlarging labels, and put sample codes plus experimental parameters in captions/CSV files.
- For SEM multi-panel figure revisions that need uniform scale-bar appearance, regenerate panels from the original TIFF/SEM sources and redraw scale bars with a fixed Arial font size, fixed visible horizontal bar length, fixed line width, and consistent position; preserve the original inferred scale labels such as `1 µm` or `2 µm`.
- Do not put long explanatory text inside the figure; put descriptions in caption or analysis documents.
- Table panels should be labeled `table` and use white cells with black gridlines, no colored fill.
- When the user provides a table screenshot and asks to preserve its format or colors, match the screenshot palette for the table while redrawing the text cleanly to avoid screenshot artifacts such as spellcheck underlines.
- For EDS C percentage point-scan group figures, do not add an in-figure statistics table unless explicitly requested; put summary statistics and conclusions in caption/analysis text instead.

## Captions and Analysis

- Captions should start with `FigN |`.
- Use English figure numbering such as `Fig1`, `Fig2`, `Fig12`, with Chinese descriptive text unless the user asks otherwise.
- Scientific descriptions should be professional, cautious, and tied to the measured data.
- For comparative analysis, calculate averages, differences, and ratios when data allow.

## Image Handling

- Preserve scale bars and make them readable.
- Remove `?` or incorrect characters in scale-bar units and render clean units such as `μm`.
- Avoid ghosted or duplicated scale bars; regenerate from the correct source if ghosting appears.
- If TIFF files fail with Pillow, convert them to PNG with a reliable local renderer, then compose from the PNG while preserving source TIFF copies.
- For EDS figures extracted from Word reports, include only the panel types requested by the reference layout; exclude extra embedded legends, screenshots, or report artifacts from the final composite.
- If EDS element maps are stored in a different order across Word reports, reorder them by element/color so the final composite matches the requested C/Si/O sequence.

## Project-Specific Scientific Preferences

- For EDS figures in this project, focus interpretation on C element content and regional uniformity.
- For Raman figures in this project, include known test conditions in captions when relevant: 532 nm laser, 0.1 s, 10 accumulations, 10 mW.
- For Raman multi-panel figures in this project, ensure D/G peak panels carry `I_D/I_G` annotations consistently; if a source panel lacks the label but raw spectra are available, compute it from baseline-corrected C-D and C-G peak heights and annotate the panel copy.
- For Raman multi-panel figures in this project, do not place experimental parameter summary boxes inside the figure unless explicitly requested; keep the figure panel-only and write material/PECVD parameters in the caption files.
- For SEM figures in this project, use the instrument name `ZEISS GeminiSEM 300 field emission scanning electron microscope` when instrument details are needed.
- For this carbon-coating project, sample codes like `6-3-3` mean June 3, parameter group 3; apply the same date/group parsing to codes such as `6-4-1` and `6-5-2` when mapping SEM/Raman/EDS panels to experiment conditions.
- For Raman files named with four digits such as `6512`, parse them as month/date/parameter-group/test-position: `6512` means June 5, parameter group 1, Raman test position 2. Each parameter-group sample usually has positions 1-3.

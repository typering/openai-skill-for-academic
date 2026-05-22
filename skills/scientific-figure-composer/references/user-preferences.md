# User Preferences for Scientific Figure Composer

This file records reusable preferences learned from the user's scientific figure-making tasks. Update it after figure tasks when the user gives a new reusable correction or style preference.

## Output Organization

- Each completed figure task should create a new folder under the report/work folder.
- Save final `.png`, final `.tif` when requested or useful for publication, `FigN_caption.txt`, and `processed_panels/`.
- When analysis text is requested, save it as `.txt`; also create `.docx` when a standalone polished document is useful.

## Figure Style

- Use compact, publication-style layouts with minimal whitespace between related panels.
- Use a white background.
- Use bold Arial panel labels `a`, `b`, `c`... placed close to the top-left of each panel.
- Increase panel-label font size when labels look small.
- Do not put long explanatory text inside the figure; put descriptions in caption or analysis documents.
- Table panels should be labeled `table` and use white cells with black gridlines, no colored fill.

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

## Project-Specific Scientific Preferences

- For EDS figures in this project, focus interpretation on C element content and regional uniformity.
- For Raman figures in this project, include known test conditions in captions when relevant: 532 nm laser, 0.1 s, 10 accumulations, 10 mW.
- For SEM figures in this project, use the instrument name `ZEISS GeminiSEM 300 field emission scanning electron microscope` when instrument details are needed.

---
name: scientific-figure-composer
description: Automatically use this skill whenever the user asks to draw, make, generate, compose, revise, or save scientific multi-panel figures or figure descriptions, even if the skill is not named. Trigger strongly on Chinese requests containing 绘制组图, 生成组图, 制作组图, 图片组图, 多图拼接, 组图描述, 图注, 图片描述, Nature布局, 论文规范, 标度尺, 光学显微镜, SEM, EDS, Raman, XRD, TEM, mapping, spectrum, table, Fig, Figure, or 图1/图2. Use it for publication-style scientific figures from PPT screenshots, microscopy/SEM/EDS/Raman/optical images, tables, and experiment notes.
metadata:
  short-description: Scientific figure panels and captions
---

# Scientific Figure Composer

Use this skill for publication-style scientific figure assembly, caption writing, and analysis-document generation from local folders, PPT/PPTX screenshots, and experimental notes.

## Automatic Invocation Rule

When the user asks for any kind of scientific figure drawing or figure composition, invoke this skill automatically without waiting for the user to name it. Treat the following as explicit triggers:

- `绘制组图`, `生成组图`, `制作组图`, `组图`, `图片组图`, `多图拼接`, `整合成一张图`
- `图注`, `图片描述`, `caption`, `Fig`, `Figure`, `图1`, `figure1`
- `Nature布局`, `论文规范`, `排版`, `标号`, `a/b/c`, `Arial`
- `标度尺`, `scale bar`, `显微镜`, `光学显微镜`, `SEM`, `EDS`, `Raman`, `XRD`, `TEM`
- Requests to create a new output folder, save finished figures, or generate txt/docx descriptions for figures

At the start of work, briefly state that this skill is being used for scientific figure composition. Then proceed directly with file inspection, figure generation, caption writing, and verification.

## Continuous Improvement Rule

This skill should improve from the user's future figure-making prompts and corrections.

When the user gives a new preference, correction, or repeated instruction during a figure task:

1. Apply it immediately to the current task.
2. Decide whether it is a reusable preference:
   - **Reusable**: layout spacing, panel-label style, output folder naming, scale-bar treatment, caption wording, table styling, analysis structure, file formats, scientific interpretation habits.
   - **Task-only**: one-off figure number, one specific image order, a temporary experiment note that does not generalize.
3. Record reusable preferences in `references/user-preferences.md` after completing the task, unless the user says not to modify the skill.
4. Promote a preference into this `SKILL.md` only when it is stable, repeated, or clearly intended as a global rule.
5. Never delete or weaken existing user preferences silently. If a new instruction conflicts with an older preference, follow the latest instruction for the current task and record the conflict/resolution.
6. In the final response, briefly mention any new reusable rule that was added to the skill or preference file.

Before starting a figure task, read `references/user-preferences.md` if it exists and apply any relevant saved preferences. Keep that file concise and grouped by topic.

## Core Workflow

1. **Read context first**
   - Inspect the user-provided folder and relevant PPT/PPTX/slides/screenshots before composing.
   - Infer figure number, sample condition, characterization type, panel order, and experimental details from the conversation and local files.
   - If a PPT/PPTX file is involved, use the PowerPoint/pptx/presentations skill or runtime tools to inspect/render it.
   - Preserve prior conversation facts such as sample conditions, instrument details, Raman parameters, PECVD conditions, and previously assigned figure numbers.
   - Load `references/user-preferences.md` for saved user-specific figure preferences.

2. **Create a new output folder every time**
   - Save final products under the report/work folder, not directly inside the raw-image folder.
   - Folder name format: `FigN_组图成品_YYYYMMDD_HHMMSS` plus a short revision suffix when useful, e.g. `_修正版`, `_紧凑修正版`.
   - Include at minimum:
     - final `.png`
     - final `.tif` when publication/export is requested
     - `FigN_caption.txt`
     - `processed_panels/` containing normalized panels and source copies
   - If the user asks for analysis or PPT text refinement, also create `FigN_analysis.txt`; create `.docx` too when a Word-like document is useful.

3. **Figure layout rules**
   - Use a clean white background, compact spacing, and large panels.
   - Follow Nature-like multi-panel conventions: panel labels `a`, `b`, `c`... in bold Arial, placed close to the top-left of each panel.
   - For SEM two-row example layouts, place larger readable panel labels in a narrow white margin to the left of each image rather than above the image, with a tight but visible horizontal gap. Keep labels fully outside the image area, keep image-to-image spacing unchanged when adjusting label size, and put experimental parameters in captions or CSV files.
   - Do not leave large whitespace between related panels; align rows/columns consistently.
   - Do not print descriptive paragraph text in the figure unless the user explicitly asks. Put descriptions in caption/analysis files.
   - Tables inside figures should be labeled `table`, not a letter, unless the user explicitly wants lettered tables.
   - Tables should have white cells, black gridlines, readable text, and no colored fill unless the user specifically requests color.
   - Do not create nested cards, decorative gradients, or presentation-style title blocks for manuscript figures.
   - Prefer 600 dpi outputs for PNG/TIF; verify dimensions and DPI after export.

4. **Image and panel handling**
   - Normalize panel sizes while preserving the full scientific content, scale bars, legends, axes, and element labels.
   - For microscopy/SEM/EDS/Raman images, keep original contrast and scale bars unless the user asks for correction.
   - If an existing scale bar contains wrong characters such as `?m`, remove or replace the wrong character and render a clean unit label, e.g. `μm`.
   - If a microscopy image lacks a scale bar and a same-magnification reference exists, add a matching scale bar using the reference scale length.
   - Avoid duplicated/ghosted scale bars. If panel revision introduces ghosting, crop/rebuild from the correct source and regenerate.
   - If TIFF reading is unstable, convert TIFF to PNG with a reliable local renderer first, then compose from the converted PNG while copying the original TIFF into `processed_panels`.

5. **Scientific captions**
   - Start captions with `FigN |` exactly, not `图N`, unless the user asks otherwise.
   - Use English-style figure numbering (`Fig1`, `Fig2`, `Fig12`) and Chinese body text when the user asks for Chinese descriptions.
   - Caption pattern:
     - Identify each panel letter and what it shows.
     - Include sample condition, treatment temperature/time, substrate, characterization type, magnification, laser/test conditions, or instrument when known.
     - For EDS, explicitly mention C element content and region comparisons when C is the focus.
     - End with a concise interpretation tied to the figure data.
   - Do not overclaim. Use wording such as “表明”, “说明”, “可能与...有关”, and note limitations for EDS light-element quantification when relevant.

6. **Analysis documents**
   - When PPT screenshots contain written analysis, rewrite it into a standalone professional analysis document.
   - Structure analysis as:
     - 测试结果概述
     - 单个样品/区域分析
     - 不同条件对比
     - 结论与后续优化建议
   - Preserve the user’s core explanation, but improve terminology, logic, and quantitative comparisons.
   - For temperature comparisons, compute averages, differences, and ratios where data allow.

## Domain-Specific Notes

### Optical Microscopy

- Group panels by sample condition and magnification.
- Use labels such as 10×, 50×, 100× only in caption unless the user requests in-figure labels.
- Scale bars must be clean and non-overlapping.

### Raman

- Include test conditions in the caption when known: laser wavelength, exposure/integration time, accumulation count, and laser power.
- For the current project pattern, mention 532 nm laser, 0.1 s, 10 accumulations, and 10 mW only when the user has provided those details.
- Keep axes and peak labels visible. Remove unintended outer gray frames when composing exported plot panels.

### SEM

- Include SEM instrument details in caption/analysis when known. For this project, the accurate name previously used was `ZEISS GeminiSEM 300 field emission scanning electron microscope`.
- Preserve scale bars and avoid resizing that makes them unreadable.

### EDS

- Include SEM image(s), element maps, spectrum, and quantitative table when available.
- Prioritize C element interpretation when the user states carbon is the focus.
- Use clean white tables with no colored fill.
- For region analysis, report both `Wt%` and `At%` if available.
- Note that EDS C quantification is comparative because C is a light element and is sensitive to topography, tilt, and interaction volume.

## Output Verification Checklist

Before final response:

- Confirm final folder exists and contains expected files.
- Confirm PNG/TIF dimensions and DPI.
- Open or preview the final image if possible.
- Check panel labels are close to panels and use Arial/bold style.
- Check tables have no colored fill when that is required.
- Check captions start with `FigN |`.
- Mention any limitation or workaround, such as TIFF conversion or missing source image.

## Final Response Pattern

Respond in Chinese. Keep it concise:

- State what was generated.
- Provide the absolute output folder path.
- List key files.
- Summarize verification evidence, especially dimensions and DPI.
- Include a short scientific result summary if useful.

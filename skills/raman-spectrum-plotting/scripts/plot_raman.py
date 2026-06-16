from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
from PIL import Image, ImageDraw
from scipy import sparse
from scipy.signal import find_peaks, medfilt, savgol_filter
from scipy.sparse.linalg import spsolve


COLOR_RED = "#D00000"
COLOR_BLUE = "#0047B3"
COLOR_PURPLE = "#8A00CC"


def choose_color(label: str, source: Path) -> str:
    text = f"{label} {source.name}".lower()
    if "origin" in text or "0v" in text:
        return COLOR_PURPLE
    if text.startswith("300") and "si" not in text:
        return COLOR_RED
    return COLOR_BLUE


def baseline_als(y: np.ndarray, lam: float = 1e6, p: float = 0.01, niter: int = 10) -> np.ndarray:
    length = len(y)
    if length < 4:
        return np.zeros_like(y)

    d_matrix = sparse.diags([1, -2, 1], [0, -1, -2], shape=(length, length - 2), format="csc")
    weights = np.ones(length)
    for _ in range(niter):
        w_matrix = sparse.spdiags(weights, 0, length, length, format="csc")
        z_matrix = w_matrix + lam * (d_matrix @ d_matrix.T)
        baseline = spsolve(z_matrix, weights * y)
        weights = p * (y > baseline) + (1 - p) * (y < baseline)
    return baseline


def odd_window(requested: int | None, length: int, default: int = 61) -> int:
    if length < 7:
        return max(1, length)
    window = requested or default
    window = min(window, length if length % 2 == 1 else length - 1)
    if window % 2 == 0:
        window -= 1
    return max(7, window)


def smooth(y: np.ndarray, window: int | None = None, polyorder: int = 3) -> np.ndarray:
    window = odd_window(window, len(y))
    if window < 7:
        return y.copy()
    polyorder = min(polyorder, window - 2)
    return savgol_filter(y, window, polyorder)


def despike(y: np.ndarray, z_threshold: float = 8.0, kernel_size: int = 9) -> np.ndarray:
    kernel = odd_window(kernel_size, len(y), default=9)
    if kernel < 3:
        return y.copy()

    median_trace = medfilt(y, kernel_size=kernel)
    residual = y - median_trace
    mad = np.median(np.abs(residual - np.median(residual)))
    if mad <= np.finfo(float).eps:
        return y.copy()

    robust_sigma = 1.4826 * mad
    spike_mask = np.abs(residual) > z_threshold * robust_sigma
    cleaned = y.copy()
    cleaned[spike_mask] = median_trace[spike_mask]
    return cleaned


def fitted_trace(
    y: np.ndarray,
    smooth_window: int | None = None,
    smooth_polyorder: int = 3,
    spike_z: float = 8.0,
) -> np.ndarray:
    cleaned = despike(y, z_threshold=spike_z)
    baseline = baseline_als(cleaned)
    corrected = cleaned - baseline
    return smooth(corrected, smooth_window, smooth_polyorder) + baseline


def plot_trace(
    y: np.ndarray,
    trace_mode: str,
    smooth_window: int | None = None,
    smooth_polyorder: int = 3,
    spike_z: float = 8.0,
) -> np.ndarray:
    if trace_mode == "original":
        return y.copy()
    if trace_mode == "smoothed":
        return smooth(despike(y, z_threshold=spike_z), smooth_window, smooth_polyorder)
    if trace_mode == "fitted":
        return fitted_trace(y, smooth_window, smooth_polyorder, spike_z)
    raise ValueError(f"Unknown trace mode: {trace_mode}")


def peak_in_window(x: np.ndarray, corrected: np.ndarray, low: float, high: float, x_min: float, x_max: float):
    low = max(low, x_min)
    high = min(high, x_max)
    mask = (x >= low) & (x <= high)
    if not np.any(mask):
        return None

    window_x = x[mask]
    window_y = corrected[mask]
    index = int(np.argmax(window_y))
    return int(round(float(window_x[index]))), float(window_y[index])


def detect_peaks(
    x: np.ndarray,
    y: np.ndarray,
    x_min: float,
    x_max: float,
    smooth_window: int | None = None,
    smooth_polyorder: int = 3,
    include_general_peaks: bool = True,
) -> list[dict[str, object]]:
    smoothed = smooth(y, smooth_window, smooth_polyorder)
    corrected = smoothed - baseline_als(smoothed)

    d_peak = peak_in_window(x, corrected, 1280, 1450, x_min, x_max)
    g_peak = peak_in_window(x, corrected, 1500, 1650, x_min, x_max)

    selected: list[dict[str, object]] = []
    if include_general_peaks:
        spread = np.percentile(corrected, 99) - np.percentile(corrected, 20)
        prominence = max(2.0, spread * 0.16)
        peaks, props = find_peaks(corrected, prominence=prominence, distance=32)
        order = np.argsort(props["prominences"])[::-1]

        for item in order:
            pos = int(round(float(x[peaks[item]])))
            if pos < x_min or pos > x_max:
                continue
            if 1230 <= pos <= min(1700, x_max):
                continue
            if any(abs(pos - int(existing["pos"])) < 50 for existing in selected):
                continue
            selected.append(
                {
                    "pos": pos,
                    "kind": "peak",
                    "label": str(pos),
                    "score": float(props["prominences"][item]),
                }
            )
            if len(selected) >= 4:
                break

    if d_peak is not None:
        selected.append({"pos": d_peak[0], "kind": "C-D", "label": f"C-D\n{d_peak[0]}", "score": d_peak[1]})
    if g_peak is not None:
        selected.append({"pos": g_peak[0], "kind": "C-G", "label": f"C-G\n{g_peak[0]}", "score": g_peak[1]})

    return sorted(selected, key=lambda item: int(item["pos"]))


def parse_feature_peak(raw: str) -> dict[str, object]:
    if ":" in raw:
        pos_text, label = raw.split(":", 1)
    else:
        pos_text, label = raw, raw
    pos = float(pos_text.strip())
    label = label.strip() or str(int(round(pos)))
    return {
        "pos": pos,
        "kind": label.splitlines()[0],
        "label": label,
        "score": float("inf"),
        "manual": True,
    }


def merge_peaks(auto_peaks: list[dict[str, object]], feature_peaks: list[dict[str, object]]) -> list[dict[str, object]]:
    merged = list(feature_peaks)
    for peak in auto_peaks:
        pos = float(peak["pos"])
        if any(abs(pos - float(existing["pos"])) < 18 for existing in merged):
            continue
        merged.append(peak)
    return sorted(merged, key=lambda item: float(item["pos"]))


def load_spectrum(path: Path, x_min: float, x_max: float) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path)
    if data.ndim != 2 or data.shape[1] < 2:
        raise ValueError(f"{path} is not a two-column Raman spectrum")

    x = data[:, 0]
    y = data[:, 1].astype(float)
    mask = (x >= x_min) & (x <= x_max)
    if not np.any(mask):
        raise ValueError(f"{path} has no data points inside {x_min}-{x_max} cm^-1")
    return x[mask], y[mask]


def plot_one(
    source: Path,
    out_dir: Path,
    x_min: float,
    x_max: float,
    line_width: float,
    color_override: str | None = None,
    show_legend: bool = True,
    trace_mode: str = "fitted",
    smooth_window: int | None = None,
    smooth_polyorder: int = 3,
    spike_z: float = 8.0,
    feature_peaks: list[dict[str, object]] | None = None,
    auto_peaks: bool = True,
    include_general_peaks: bool = True,
    output_stem: str | None = None,
) -> tuple[Path, list[dict[str, object]]]:
    label = source.stem
    color = color_override or choose_color(label, source)
    x, y = load_spectrum(source, x_min, x_max)
    display_y = plot_trace(y, trace_mode, smooth_window, smooth_polyorder, spike_z)
    peaks = (
        detect_peaks(x, display_y, x_min, x_max, smooth_window, smooth_polyorder, include_general_peaks)
        if auto_peaks
        else []
    )
    peaks = merge_peaks(peaks, feature_peaks or [])

    fig, ax = plt.subplots(figsize=(6.4, 4.8), dpi=600)
    ax.plot(x, display_y, color=color, linewidth=line_width, label=label)

    ymin = float(np.min(display_y))
    ymax = float(np.max(display_y))
    yrange = max(1.0, ymax - ymin)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(ymin - 0.08 * yrange, ymax + 0.30 * yrange)

    label_y = ymax + 0.18 * yrange
    for index, peak in enumerate(peaks):
        x0 = float(peak["pos"])
        is_carbon = str(peak["kind"]).startswith("C-")
        ax.axvline(
            x0,
            color="black",
            linestyle=(0, (1, 3)),
            linewidth=1.1 if is_carbon else 0.9,
            alpha=0.95,
        )
        text_x = min(x0, x_max - 8)
        ha = "right" if x0 > x_max - 45 else "center"
        ax.text(
            text_x,
            label_y,
            str(peak["label"]),
            ha=ha,
            va="bottom",
            fontsize=9.5 if is_carbon else 9,
            fontweight="bold",
            color="black",
            linespacing=0.9,
        )

    ax.set_xlabel(r"Raman Shift (cm$^{-1}$)", fontsize=16, fontweight="bold")
    ax.set_ylabel("Raman Intensity (offset)", fontsize=15, fontweight="bold")
    ax.set_xticks(make_major_ticks(x_min, x_max))
    ax.xaxis.set_minor_locator(MultipleLocator(100))
    ax.tick_params(axis="x", which="major", direction="in", length=5, width=1.2, labelsize=10)
    ax.tick_params(axis="x", which="minor", direction="in", length=3, width=1.0)
    ax.tick_params(axis="y", which="major", direction="in", length=5, width=1.2, labelleft=False)

    for tick in ax.get_xticklabels():
        tick.set_fontname("Times New Roman")
        tick.set_fontweight("bold")
    for spine in ax.spines.values():
        spine.set_linewidth(1.6)
        spine.set_color("black")

    if show_legend:
        legend = ax.legend(loc="upper right", frameon=True, fontsize=8, handlelength=2.8)
        legend.get_frame().set_edgecolor("black")
        legend.get_frame().set_linewidth(0.8)
        legend.get_frame().set_alpha(1.0)

    fig.tight_layout(pad=1.1)
    stem = output_stem or label
    png_path = out_dir / f"{stem}_Raman_peaks.png"
    svg_path = out_dir / f"{stem}_Raman_peaks.svg"
    fig.savefig(png_path, dpi=600, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)
    return png_path, peaks


def make_major_ticks(x_min: float, x_max: float) -> list[int]:
    if math.isclose(x_min, 0) and math.isclose(x_max, 1600):
        return [0, 400, 800, 1200, 1600]
    if x_max <= 2000:
        return [tick for tick in [200, 600, 1000, 1400, 1800, 2000] if x_min <= tick <= x_max]
    step = 400
    start = int(math.ceil(x_min / step) * step)
    return list(range(start, int(x_max) + 1, step))


def make_contact_sheet(paths: list[Path], output: Path) -> None:
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((420, 315))
        canvas = Image.new("RGB", (440, 350), "white")
        canvas.paste(image, ((440 - image.width) // 2, 26))
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 6), path.name, fill=(0, 0, 0))
        thumbs.append(canvas)

    cols = 2
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 440, rows * 350), "white")
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % cols) * 440, (index // cols) * 350))
    sheet.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Raman spectra with peak annotations.")
    parser.add_argument("files", nargs="+", type=Path, help="Two-column Raman .txt files.")
    parser.add_argument("--out-dir", type=Path, default=Path("processed_raman_plots"))
    parser.add_argument("--x-min", type=float, default=0)
    parser.add_argument("--x-max", type=float, default=1600)
    parser.add_argument("--line-width", type=float, default=2.15)
    parser.add_argument("--color", help="Override the curve color, for example #0047B3.")
    parser.add_argument("--no-legend", action="store_true", help="Hide the sample legend/图注.")
    parser.add_argument(
        "--trace-mode",
        choices=["original", "smoothed", "fitted"],
        default="fitted",
        help="Plot raw, despiked smoothed, or baseline-preserving fitted/smoothed trace.",
    )
    parser.add_argument("--smooth-window", type=int, help="Savitzky-Golay smoothing window; odd values work best.")
    parser.add_argument("--smooth-polyorder", type=int, default=3)
    parser.add_argument("--spike-z", type=float, default=8.0, help="Robust z threshold for single-point spike replacement.")
    parser.add_argument(
        "--feature-peak",
        action="append",
        default=[],
        help="Manually annotate a feature peak as position:label, e.g. 796:SiC-TO. Can be repeated.",
    )
    parser.add_argument("--no-auto-peaks", action="store_true", help="Only use manually provided feature peaks.")
    parser.add_argument(
        "--carbon-only",
        action="store_true",
        help="Auto-detect only C-D and C-G bands, suppressing miscellaneous peak labels.",
    )
    parser.add_argument("--output-stem", help="Custom output filename stem. Only valid with one input file.")
    parser.add_argument("--no-contact-sheet", action="store_true")
    args = parser.parse_args()

    if args.output_stem and len(args.files) != 1:
        parser.error("--output-stem can only be used with exactly one input file")

    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "mathtext.fontset": "stix",
            "axes.unicode_minus": False,
        }
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    feature_peaks = [parse_feature_peak(item) for item in args.feature_peak]

    peak_rows = [["sample", "source_file", "peak_type", "raman_shift_cm-1"]]
    png_paths = []
    for source in args.files:
        png_path, peaks = plot_one(
            source,
            args.out_dir,
            args.x_min,
            args.x_max,
            args.line_width,
            color_override=args.color,
            show_legend=not args.no_legend,
            trace_mode=args.trace_mode,
            smooth_window=args.smooth_window,
            smooth_polyorder=args.smooth_polyorder,
            spike_z=args.spike_z,
            feature_peaks=feature_peaks,
            auto_peaks=not args.no_auto_peaks,
            include_general_peaks=not args.carbon_only,
            output_stem=args.output_stem,
        )
        png_paths.append(png_path)
        for peak in peaks:
            peak_rows.append([source.stem, str(source), peak["kind"], peak["pos"]])

    with (args.out_dir / "peak_positions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerows(peak_rows)

    if not args.no_contact_sheet and len(png_paths) > 1:
        make_contact_sheet(png_paths, args.out_dir / "contact_sheet.png")

    print(f"Saved {len(png_paths)} Raman figures to {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()

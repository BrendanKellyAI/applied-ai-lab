"""Brand chart system (specification section 5.8), so charts drop straight into decks.

Each chart is drawn by a function that receives a figure, axes, and style, and is exported at
slide size (PNG and SVG) and article size (PNG). Export refuses charts that break the rules:
titles inside the image, more than one acid green element, labels below the minimum size, or a
missing unit or sample size.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.artist import Artist  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_hex  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from matplotlib.ticker import Formatter, PercentFormatter  # noqa: E402

NAVY = "#0B1F3A"
WHITE = "#FFFFFF"
MIST = "#C9D3E0"
SLATE = "#8193AD"
ACID_GREEN = "#B8E04A"

PREFERRED_FONT = "Inter Tight"
DPI = 100
MIN_LABEL_PX_AT_1080 = 32
FINDING_GID = "finding"
SERIES_COLOURS = (MIST, SLATE)
SERIES_HATCHES = ("", "//")
LINE_STYLES = ("-", "--", ":", "-.")
# Space kept clear at the image edges, as a fraction of width and height.
EDGE_MARGIN = 0.03


@dataclass(frozen=True)
class ChartLayout:
    name: str
    width_px: int
    height_px: int
    formats: tuple[str, ...]


SLIDE = ChartLayout("slide", 1080, 1350, ("png", "svg"))
ARTICLE = ChartLayout("article", 1920, 1080, ("png",))


@dataclass(frozen=True)
class ChartSpec:
    name: str
    units: str
    sample_size: str
    # Set when the chart has a highlight rule but no element met it; the chart then says so.
    no_highlight_note: str | None = None
    # An extra footer line, for a caveat a reader needs in order to read the chart correctly.
    # Keep each line to about 60 characters: the footer does not wrap.
    footnote: str | None = None

    def __post_init__(self) -> None:
        if not self.units.strip():
            raise ValueError("Every chart must state its units")
        if not self.sample_size.strip():
            raise ValueError("Every chart must state its sample size")


@dataclass(frozen=True)
class ChartStyle:
    layout: ChartLayout
    label_pt: float
    line_width_pt: float


def label_size_pt(layout: ChartLayout) -> float:
    """Minimum label size: 32 px at 1080 px wide, scaled with width, in points."""
    pixels = MIN_LABEL_PX_AT_1080 * layout.width_px / 1080
    return pixels * 72 / DPI


@cache
def font_family() -> tuple[str, ...]:
    installed = {font.name for font in font_manager.fontManager.ttflist}
    return (PREFERRED_FONT,) if PREFERRED_FONT in installed else ("sans-serif",)


def sequential_colormap() -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list("slate_to_white", [SLATE, WHITE])


def _rc(style: ChartStyle) -> dict[str, object]:
    size = style.label_pt
    return {
        "font.family": list(font_family()),
        "font.size": size,
        "axes.labelsize": size,
        "xtick.labelsize": size,
        "ytick.labelsize": size,
        "legend.fontsize": size,
        "figure.facecolor": NAVY,
        "axes.facecolor": NAVY,
        "savefig.facecolor": NAVY,
        "axes.edgecolor": SLATE,
        "axes.labelcolor": WHITE,
        "text.color": MIST,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "xtick.labelcolor": MIST,
        "ytick.labelcolor": MIST,
        "grid.color": SLATE,
        "legend.frameon": False,
        "legend.labelcolor": MIST,
        "hatch.color": NAVY,
        "svg.fonttype": "path",
        # A fixed salt makes the IDs inside an SVG the same on every render, so re-rendering an
        # unchanged chart leaves the committed file unchanged.
        "svg.hashsalt": "applied-ai-lab",
    }


def highlight(artist: Artist) -> Artist:
    """Mark the one element that shows the finding in acid green."""
    if isinstance(artist, Line2D):
        artist.set_color(ACID_GREEN)
    elif isinstance(artist, Patch) and artist.get_fill():
        artist.set_facecolor(ACID_GREEN)
    elif isinstance(artist, Patch):
        artist.set_edgecolor(ACID_GREEN)
    elif isinstance(artist, Text):
        artist.set_color(ACID_GREEN)
    else:
        raise TypeError(f"Cannot highlight {type(artist).__name__}")
    artist.set_gid(FINDING_GID)
    return artist


def heatmap(
    ax: Axes,
    values: Sequence[Sequence[float]],
    *,
    row_labels: Sequence[str],
    col_labels: Sequence[str],
    style: ChartStyle,
    highlight_cell: tuple[int, int] | None = None,
    value_format: str = "{:.0%}",
) -> None:
    """Values from 0 to 1, shown in each cell, on a slate to white scale."""
    ax.imshow(values, cmap=sequential_colormap(), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(col_labels)), labels=col_labels)
    ax.set_yticks(range(len(row_labels)), labels=row_labels)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row, row_values in enumerate(values):
        for col, value in enumerate(row_values):
            ax.text(col, row, value_format.format(value), ha="center", va="center", color=NAVY)
    if highlight_cell is not None:
        row, col = highlight_cell
        outline = Rectangle(
            (col - 0.5, row - 0.5), 1, 1, fill=False, linewidth=style.line_width_pt, clip_on=False
        )
        ax.add_patch(outline)
        highlight(outline)


def grouped_bars(
    ax: Axes,
    *,
    categories: Sequence[str],
    series: Sequence[tuple[str, Sequence[float]]],
    style: ChartStyle,
    highlight_bar: tuple[int, int] | None = None,
    value_formatter: Formatter | None = None,
) -> None:
    """Bars grouped by category, with series told apart by colour, hatching, and legend.

    Values are proportions on a percentage axis unless `value_formatter` says otherwise, which
    is what a chart of multiples rather than shares needs.
    """
    if len(series) > len(SERIES_COLOURS):
        raise ValueError(f"At most {len(SERIES_COLOURS)} series are supported")
    width = 0.8 / len(series)
    for index, (label, values) in enumerate(series):
        offsets = [i - 0.4 + width * (index + 0.5) for i in range(len(categories))]
        bars = ax.bar(
            offsets,
            values,
            width=width,
            label=label,
            color=SERIES_COLOURS[index],
            hatch=SERIES_HATCHES[index],
            edgecolor=NAVY,
        )
        if highlight_bar is not None and highlight_bar[0] == index:
            highlight(bars.patches[highlight_bar[1]])
    ax.set_xticks(range(len(categories)), labels=categories)
    ax.yaxis.set_major_formatter(value_formatter or PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", alpha=0.4)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    # A single series needs no legend: the axis label already says what the bars measure.
    if len(series) > 1:
        # Built from fresh swatches rather than from the bars themselves. Matplotlib copies the
        # face colour of the first bar in a series into its legend key, so a highlighted first
        # bar would turn its legend swatch acid green too, and the chart would show the finding
        # twice.
        ax.legend(
            handles=[
                Patch(
                    facecolor=SERIES_COLOURS[index],
                    hatch=SERIES_HATCHES[index],
                    edgecolor=NAVY,
                    label=label,
                )
                for index, (label, _) in enumerate(series)
            ],
            loc="upper left",
            bbox_to_anchor=(0, 1.12),
            ncols=len(series),
        )


def _is_acid_green(artist: Artist) -> bool:
    """Whether an artist is drawn in acid green, however it came to be.

    Checked by colour rather than by the marker `highlight` leaves, because matplotlib copies
    colours into artists of its own, such as legend keys, without copying the marker.
    """
    if isinstance(artist, Line2D):
        return _is_acid(artist.get_color())
    if isinstance(artist, Patch):
        return _is_acid(artist.get_facecolor() if artist.get_fill() else artist.get_edgecolor())
    if isinstance(artist, Text):
        return _is_acid(artist.get_color())
    return False


def _is_acid(colour: object) -> bool:
    try:
        return to_hex(colour).upper() == ACID_GREEN.upper()
    except ValueError:  # pragma: no cover - matplotlib colours are always convertible
        return False


def _check(fig: Figure, spec: ChartSpec, style: ChartStyle) -> None:
    for ax in fig.axes:
        if any(ax.get_title(loc=loc) for loc in ("left", "center", "right")):
            raise ValueError("Titles belong on the slide, not inside the chart image")
    suptitle = getattr(fig, "_suptitle", None)
    if suptitle is not None and suptitle.get_text():
        raise ValueError("Titles belong on the slide, not inside the chart image")
    findings = fig.findobj(_is_acid_green)
    if len(findings) > 1:
        raise ValueError(f"Only one acid green element per chart; found {len(findings)}")
    if findings and spec.no_highlight_note:
        raise ValueError("A chart with a highlighted finding cannot also set no_highlight_note")
    for text in fig.findobj(Text):
        visible = text.get_visible() and text.get_text().strip()
        if visible and text.get_fontsize() < style.label_pt - 0.01:
            raise ValueError(
                f"Label '{text.get_text()[:30]}' is smaller than the minimum "
                f"{style.label_pt:.1f} pt"
            )


def _render(
    draw: Callable[[Figure, Axes, ChartStyle], None],
    layout: ChartLayout,
    spec: ChartSpec,
    out_dir: Path,
) -> list[Path]:
    style = ChartStyle(
        layout=layout,
        label_pt=label_size_pt(layout),
        line_width_pt=label_size_pt(layout) / 4,
    )
    footer = f"{spec.units} · {spec.sample_size}"
    if spec.footnote:
        footer = f"{spec.footnote}\n{footer}"
    if spec.no_highlight_note:
        footer = f"{spec.no_highlight_note}\n{footer}"
    footer_lines = footer.count("\n") + 1
    footer_fraction = (footer_lines + 1) * style.label_pt * DPI / 72 / layout.height_px
    with plt.rc_context(_rc(style)):
        fig = plt.figure(
            figsize=(layout.width_px / DPI, layout.height_px / DPI), dpi=DPI, layout="constrained"
        )
        try:
            ax = fig.add_subplot()
            draw(fig, ax, style)
            fig.text(0.02, footer_fraction / 2, footer, va="center", color=MIST)
            _check(fig, spec, style)
            fig.get_layout_engine().set(
                rect=(
                    EDGE_MARGIN,
                    footer_fraction,
                    1 - 2 * EDGE_MARGIN,
                    1 - footer_fraction - EDGE_MARGIN,
                )
            )
            paths = []
            for extension in layout.formats:
                path = out_dir / f"{spec.name}-{layout.name}.{extension}"
                # No creation date in the file, for the same reason.
                metadata = {"Date": None} if extension == "svg" else None
                fig.savefig(path, dpi=DPI, format=extension, metadata=metadata)
                paths.append(path)
            return paths
        finally:
            plt.close(fig)


def export_chart(
    draw: Callable[[Figure, Axes, ChartStyle], None],
    out_dir: Path,
    spec: ChartSpec,
    layouts: Sequence[ChartLayout] = (SLIDE, ARTICLE),
) -> list[Path]:
    """Render `draw` at each layout and save it. Returns the files written."""
    out_dir.mkdir(parents=True, exist_ok=True)
    return [path for layout in layouts for path in _render(draw, layout, spec, out_dir)]

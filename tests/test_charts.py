"""Sample charts rendered from dummy data and checked against specification section 5.8."""

import matplotlib
import pytest
from PIL import Image

from lab.charts import (
    ACID_GREEN,
    ARTICLE,
    MIST,
    NAVY,
    SLATE,
    SLIDE,
    ChartSpec,
    export_chart,
    grouped_bars,
    heatmap,
    highlight,
    label_size_pt,
)

matplotlib.use("Agg")


def _hex_to_rgb(colour: str) -> tuple[int, int, int]:
    return tuple(int(colour[i : i + 2], 16) for i in (1, 3, 5))


def draw_heatmap(fig, ax, style):
    values = [
        [1.0, 0.83, 0.5, 0.67, 1.0],
        [1.0, 0.67, 0.33, 0.5, 0.83],
        [0.83, 0.5, 0.17, 0.33, 1.0],
    ]
    heatmap(
        ax,
        values,
        row_labels=["4k", "16k", "64k"],
        col_labels=["0%", "25%", "50%", "75%", "100%"],
        style=style,
        highlight_cell=(2, 2),
    )
    ax.set_xlabel("Fact position")
    ax.set_ylabel("Context length (tokens)")


def draw_bars(fig, ax, style):
    grouped_bars(
        ax,
        categories=["T1", "T2", "T3", "T4"],
        series=[("Lowest", [0.9, 0.6, 0.4, 0.3]), ("High", [0.9, 0.8, 0.7, 0.4])],
        style=style,
        highlight_bar=(1, 2),
    )
    ax.set_ylabel("Accuracy (%)")


HEATMAP_SPEC = ChartSpec(name="heatmap", units="Accuracy (%)", sample_size="n = 6 per cell")


@pytest.fixture
def exported(tmp_path):
    return export_chart(draw_heatmap, tmp_path, HEATMAP_SPEC)


def test_exports_slide_png_and_svg_and_article_png(exported, tmp_path):
    names = sorted(path.name for path in exported)

    assert names == ["heatmap-article.png", "heatmap-slide.png", "heatmap-slide.svg"]


def test_png_sizes_match_specification(tmp_path, exported):
    with Image.open(tmp_path / "heatmap-slide.png") as slide:
        assert slide.size == (SLIDE.width_px, SLIDE.height_px) == (1080, 1350)
    with Image.open(tmp_path / "heatmap-article.png") as article:
        assert article.size == (ARTICLE.width_px, ARTICLE.height_px) == (1920, 1080)


def test_background_is_navy(tmp_path, exported):
    with Image.open(tmp_path / "heatmap-slide.png") as image:
        assert image.convert("RGB").getpixel((2, 2)) == _hex_to_rgb(NAVY)


def test_acid_green_outline_is_drawn(tmp_path, exported):
    with Image.open(tmp_path / "heatmap-slide.png") as image:
        colours = {colour for _count, colour in image.convert("RGB").getcolors(maxcolors=2**20)}

    assert _hex_to_rgb(ACID_GREEN) in colours


def test_svg_has_navy_background_and_text_as_paths(tmp_path, exported):
    svg = (tmp_path / "heatmap-slide.svg").read_text(encoding="utf-8").lower()

    assert NAVY.lower() in svg
    assert "<text" not in svg


def test_label_size_is_32_pixels_at_1080_width():
    # 32 px at 100 dpi is 23.04 pt; the article layout scales with width
    assert label_size_pt(SLIDE) == pytest.approx(23.04)
    assert label_size_pt(ARTICLE) == pytest.approx(23.04 * 1920 / 1080)


def test_titles_inside_the_image_are_refused(tmp_path):
    def with_title(fig, ax, style):
        draw_heatmap(fig, ax, style)
        ax.set_title("Accuracy by position")

    with pytest.raises(ValueError, match="Titles belong on the slide"):
        export_chart(with_title, tmp_path, HEATMAP_SPEC)


def test_more_than_one_acid_green_element_is_refused(tmp_path):
    def two_findings(fig, ax, style):
        draw_bars(fig, ax, style)
        highlight(ax.patches[0])

    with pytest.raises(ValueError, match="one acid green element"):
        export_chart(two_findings, tmp_path, ChartSpec("bars", "Accuracy (%)", "n = 30"))


def test_small_labels_are_refused(tmp_path):
    def tiny(fig, ax, style):
        draw_bars(fig, ax, style)
        ax.text(0, 0.5, "footnote", fontsize=8)

    with pytest.raises(ValueError, match="smaller than"):
        export_chart(tiny, tmp_path, ChartSpec("bars", "Accuracy (%)", "n = 30"))


def test_units_and_sample_size_are_required():
    with pytest.raises(ValueError, match="units"):
        ChartSpec("bars", units="", sample_size="n = 30")
    with pytest.raises(ValueError, match="sample size"):
        ChartSpec("bars", units="Accuracy (%)", sample_size=" ")


def test_chart_with_no_finding_says_so(tmp_path):
    def no_finding(fig, ax, style):
        grouped_bars(
            ax,
            categories=["T1", "T2"],
            series=[("Lowest", [0.5, 0.6]), ("High", [0.5, 0.6])],
            style=style,
        )

    spec = ChartSpec("bars", "Accuracy (%)", "n = 30", no_highlight_note="No task met the rule")
    export_chart(no_finding, tmp_path, spec, layouts=(SLIDE,))

    with pytest.raises(ValueError, match="no_highlight_note"):
        export_chart(draw_bars, tmp_path, spec, layouts=(SLIDE,))


def test_series_are_distinguished_by_more_than_colour(tmp_path):
    captured = {}

    def capture(fig, ax, style):
        draw_bars(fig, ax, style)
        captured["hatches"] = {patch.get_hatch() for patch in ax.patches}
        captured["legend"] = [text.get_text() for text in ax.get_legend().get_texts()]
        captured["colours"] = {
            matplotlib.colors.to_hex(patch.get_facecolor()).upper() for patch in ax.patches
        }

    export_chart(capture, tmp_path, ChartSpec("bars", "Accuracy (%)", "n = 30"), layouts=(SLIDE,))

    assert len(captured["hatches"]) == 2
    assert captured["legend"] == ["Lowest", "High"]
    assert captured["colours"] == {MIST.upper(), SLATE.upper(), ACID_GREEN.upper()}


def test_a_footnote_adds_a_footer_line(tmp_path):
    captured = {}

    def capture(fig, ax, style):
        draw_bars(fig, ax, style)
        captured["fig"] = fig

    spec = ChartSpec("bars", "Accuracy (%)", "n = 30", footnote="Lowest is minimal on one model")
    export_chart(capture, tmp_path, spec, layouts=(SLIDE,))

    footers = [
        text.get_text()
        for text in captured["fig"].texts
        if "Lowest is minimal on one model" in text.get_text()
    ]
    assert footers == ["Lowest is minimal on one model\nAccuracy (%) · n = 30"]


def test_bars_can_show_a_multiple_rather_than_a_percentage(tmp_path):
    captured = {}

    def multiples(fig, ax, style):
        grouped_bars(
            ax,
            categories=["T1", "T2"],
            series=[("High", [4.0, 12.0])],
            style=style,
            value_formatter=matplotlib.ticker.FuncFormatter(lambda value, _: f"{value:g}x"),
        )
        captured["labels"] = [label.get_text() for label in ax.get_yticklabels()]
        captured["legend"] = ax.get_legend()

    export_chart(multiples, tmp_path, ChartSpec("bars", "Multiple", "n = 30"), layouts=(SLIDE,))

    assert any(label.endswith("x") for label in captured["labels"] if label)
    assert captured["legend"] is None


def test_highlighting_the_first_bar_does_not_recolour_its_legend_key(tmp_path):
    captured = {}

    def highlight_first(fig, ax, style):
        grouped_bars(
            ax,
            categories=["T1", "T2"],
            series=[("Lowest", [0.5, 0.6]), ("High", [0.9, 0.6])],
            style=style,
            highlight_bar=(1, 0),
        )
        captured["legend"] = [
            matplotlib.colors.to_hex(handle.get_facecolor()).upper()
            for handle in ax.get_legend().legend_handles
        ]

    export_chart(
        highlight_first, tmp_path, ChartSpec("bars", "Accuracy (%)", "n = 30"), layouts=(SLIDE,)
    )

    assert ACID_GREEN.upper() not in captured["legend"]


def test_a_second_acid_green_element_is_refused_even_without_the_marker(tmp_path):
    def two_greens(fig, ax, style):
        draw_bars(fig, ax, style)
        # Coloured by hand rather than through highlight(), so it carries no marker.
        ax.patches[0].set_facecolor(ACID_GREEN)

    with pytest.raises(ValueError, match="one acid green element"):
        export_chart(two_greens, tmp_path, ChartSpec("bars", "Accuracy (%)", "n = 30"))

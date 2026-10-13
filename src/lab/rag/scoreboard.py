"""The season scoreboard: one row per episode, its four numbers before and after its change,
and whether the change joined the reference system. Kept in season2/scoreboard.json.

The pipeline strip on the scoreboard chart numbers the eleven stages; the stage an episode
changed is the one acid green element. E2 changes no stage, so its strip highlights nothing.
"""

import json
from pathlib import Path
from typing import Any

import yaml
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import FancyBboxPatch
from pydantic import BaseModel, ConfigDict

from lab.charts import MIST, NAVY, SLATE, ChartSpec, ChartStyle, export_chart, highlight
from lab.rag.config import STAGES
from lab.rag.score import SeasonNumbers

NUMBERS = ("search", "answer", "not_found", "leaks")
LABELS = {"search": "Search", "answer": "Answer", "not_found": "Not found", "leaks": "Leaks"}
STRIP = ("Load", *[s.title() for s in STAGES])


class Row(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    episode: str
    stage_changed: str | None
    config_before: str | None
    config_after: str
    before: SeasonNumbers | None
    after: SeasonNumbers
    joined: bool
    models_returned: dict[str, Any]
    corpus_version: str


def load_rows(path: Path) -> list[Row]:
    if not path.exists():
        return []
    return [Row.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8"))]


def record(path: Path, row: Row) -> list[Row]:
    """Add or replace the episode's row, keeping episode order. Returns the new rows."""
    rows = [r for r in load_rows(path) if r.episode != row.episode] + [row]
    rows.sort(key=lambda r: _episode_number(r.episode))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([r.model_dump(mode="json") for r in rows], indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return rows


def _episode_number(episode: str) -> int:
    return int(episode.split("-")[1].removeprefix("e"))


def draw_scoreboard(row: Row):
    """A draw function for export_chart: the strip, then the four numbers before and after."""

    def draw(fig: Figure, ax: Axes, style: ChartStyle) -> None:
        ax.set_axis_off()
        ax.set_xlim(0, len(STRIP))
        ax.set_ylim(0, 1)
        changed = STAGES.get(row.stage_changed) if row.stage_changed else None
        for n in range(len(STRIP)):
            box = FancyBboxPatch(
                (n + 0.08, 0.84),
                0.84,
                0.12,
                boxstyle="round,pad=0.01",
                facecolor=MIST,
                edgecolor=NAVY,
            )
            ax.add_patch(box)
            if changed == n + 1:
                highlight(box)
            ax.text(n + 0.5, 0.9, str(n + 1), ha="center", va="center", color=NAVY)
        bars = ax.inset_axes((0.28, 0.0, 0.72, 0.74))
        _number_bars(bars, row)

    return draw


def _number_bars(ax: Axes, row: Row) -> None:
    labels = [LABELS[n] for n in NUMBERS]
    positions = list(range(len(NUMBERS)))[::-1]
    series = [("Before", row.before), ("After", row.after)] if row.before else [("", row.after)]
    height = 0.8 / len(series)
    for index, (label, numbers) in enumerate(series):
        values = [getattr(numbers, n).rate for n in NUMBERS]
        offsets = [p + 0.4 - height * (index + 0.5) for p in positions]
        ax.barh(
            offsets, values, height=height, color=(SLATE, MIST)[index], edgecolor=NAVY, label=label
        )
        for y, value in zip(offsets, values, strict=True):
            ax.text(value + 0.02, y, f"{value:.0%}", va="center", color=MIST)
    if len(series) > 1:
        ax.legend(loc="lower right", frameon=False, labelcolor=MIST)
    ax.set_yticks(positions, labels=labels)
    ax.set_xlim(0, 1.25)
    ax.set_xticks([])
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)


def export_scoreboard(row: Row, out_dir: Path, sample: str) -> list[Path]:
    stage = row.stage_changed.title() if row.stage_changed else "none"
    spec = ChartSpec(
        name="scoreboard",
        units="Share of items",
        sample_size=sample,
        no_highlight_note=None if row.stage_changed else "Baseline: no stage changed",
        # Leaks are a share of public-asker items, not of every item.
        footnote=f"Stage changed: {stage} · leaks: of public items",
    )
    return export_chart(draw_scoreboard(row), out_dir, spec)


def record_history(path: Path, entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Add or replace an episode's entry in season2/reference_history.yaml."""
    entries = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else []
    entries = [e for e in entries or [] if e["episode"] != entry["episode"]] + [entry]
    entries.sort(key=lambda e: _episode_number(e["episode"]))
    path.write_text(yaml.safe_dump(entries, sort_keys=False), encoding="utf-8", newline="\n")
    return entries

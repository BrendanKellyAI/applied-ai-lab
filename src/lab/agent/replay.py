"""`lab agent replay`: one case's trajectory as Markdown and as a slide-ready SVG. No calls.

Every model turn, every tool call with its arguments, every result and every harness decision,
in order, so a deck can step one case through an arm.
"""

import json
from html import escape
from pathlib import Path

from lab.agent.loop import CaseRun

RESULT_CHARS = 280
SVG_WIDTH = 1600
LINE_HEIGHT = 34
WRAP = 110


def load_run(runs_path: Path, case_id: str, repeat: int = 0) -> CaseRun:
    for line in runs_path.read_text(encoding="utf-8").splitlines():
        run = CaseRun.model_validate_json(line)
        if run.case_id == case_id and run.repeat == repeat:
            return run
    raise KeyError(f"{case_id} (repeat {repeat}) is not in {runs_path}")


def _short(text: str, limit: int = RESULT_CHARS) -> str:
    return text if len(text) <= limit else text[:limit] + " ..."


def _args(arguments_json: str) -> str:
    try:
        args = json.loads(arguments_json)
    except json.JSONDecodeError:
        return arguments_json
    return ", ".join(f"{k}={v!r}" for k, v in args.items() if v is not None)


MARKS = {
    "ok": "",
    "tool_error": " (error)",
    "blocked": " (BLOCKED by the harness)",
    "malformed": " (malformed)",
}


def lines(run: CaseRun) -> list[tuple[str, str]]:
    """(style, text) pairs: turn headings, model text, calls and results, in order."""
    out: list[tuple[str, str]] = []
    events = {}
    for event in run.events:
        events.setdefault(event.turn, []).append(event)
    for turn in run.turns:
        tokens = f"{turn.input_tokens:,} tokens in, {turn.output_tokens:,} out"
        heading = f"Turn {turn.index + 1}: {tokens}"
        out.append(("turn", heading))
        if turn.text.strip():
            out.append(("model", f"Model: {_short(turn.text.strip())}"))
        for event in events.get(turn.index, []):
            call = f"{event.name}({_args(event.arguments_json)})"
            out.append(("call", f"Calls {call}{MARKS[event.outcome]}"))
            out.append(("result", f"Result: {_short(event.result_json)}"))
    out.append(("turn", f"Stopped: {run.stop_reason}"))
    return out


def markdown(run: CaseRun) -> str:
    text = [f"# Case {run.case_id}, arm {run.arm}", ""]
    for style, line in lines(run):
        if style == "turn":
            text += ["", f"## {line}", ""]
        elif style == "result":
            text.append(f"  - {line}")
        else:
            text.append(f"- {line}")
    return "\n".join(text).strip() + "\n"


def svg(run: CaseRun) -> str:
    """A tall slide-ready list: turns in bold, calls in the accent colour, results muted."""
    colours = {"turn": "#111111", "model": "#333333", "call": "#1f5fbf", "result": "#666666"}
    rows: list[tuple[str, str]] = []
    for style, line in lines(run):
        for start in range(0, max(len(line), 1), WRAP):
            rows.append((style, line[start : start + WRAP]))
    height = LINE_HEIGHT * (len(rows) + 2)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{height}" '
        f'viewBox="0 0 {SVG_WIDTH} {height}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{SVG_WIDTH}" height="{height}" fill="#ffffff"/>',
    ]
    for index, (style, text) in enumerate(rows, start=1):
        weight = "bold" if style == "turn" else "normal"
        indent = 40 if style in ("turn", "model") else 80
        parts.append(
            f'<text x="{indent}" y="{index * LINE_HEIGHT + 10}" font-size="22" '
            f'fill="{colours[style]}" font-weight="{weight}">{escape(text)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def write_replay(run: CaseRun, folder: Path) -> tuple[Path, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"replay-{run.arm}-{run.case_id}"
    md, image = folder / f"{stem}.md", folder / f"{stem}-slide.svg"
    md.write_text(markdown(run), encoding="utf-8", newline="\n")
    image.write_text(svg(run), encoding="utf-8", newline="\n")
    return md, image

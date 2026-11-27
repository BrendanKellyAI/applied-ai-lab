"""`lab agent`: the Season 5 case environment and agent runs."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer

from lab.agent.build import SEED, build_dataset

agent_app = typer.Typer(help="Season 5: the Halvard case environment and agent runs.")


@agent_app.command("build-world")
def build_world_command(
    root: Annotated[Path, typer.Option(help="Repository root to write under.")] = Path("."),
    seed: Annotated[int, typer.Option(help="Random seed for the world and cases.")] = SEED,
) -> None:
    """Build the case world, case facts, images and telemetry logs. No model calls."""
    summary = build_dataset(root, seed)
    typer.echo(json.dumps(asdict(summary), indent=2))

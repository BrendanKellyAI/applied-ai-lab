"""Command line entry point for the lab harness.

Commands (smoke, estimate, run, analyse) are added in later build phases.
"""

import typer

from lab import __version__

app = typer.Typer(help="Run and analyse applied-ai-lab experiments.", no_args_is_help=True)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"applied-ai-lab {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the harness version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
) -> None:
    """Run and analyse applied-ai-lab experiments."""

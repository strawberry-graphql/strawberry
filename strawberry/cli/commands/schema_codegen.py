from pathlib import Path

import typer

from strawberry.cli.app import app
from strawberry.schema_codegen import codegen
from strawberry.schema_codegen.config import load_config


@app.command(help="Generate code from a query")
def schema_codegen(
    schema: Path = typer.Argument(exists=True),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        file_okay=True,
        dir_okay=False,
        writable=True,
        resolve_path=True,
    ),
    config: Path | None = typer.Option(
        None,
        "-c",
        "--config",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="YAML config file (e.g. scalar overrides).",
    ),
) -> None:
    scalar_overrides: dict[str, str] | None = None
    if config is not None:
        try:
            scalar_overrides = load_config(config).scalars or None
        except (ValueError, TypeError) as exc:
            raise typer.BadParameter(str(exc), param_hint="--config") from exc

    generated_output = codegen(schema.read_text(), scalar_overrides=scalar_overrides)

    if output is None:
        typer.echo(generated_output)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generated_output)

    typer.echo(f"Code generated at `{output.name}`")

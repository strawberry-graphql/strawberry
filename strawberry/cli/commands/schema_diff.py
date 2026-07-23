from pathlib import Path

import rich
import rich.markup
import typer
from graphql.error import GraphQLError

from strawberry.cli.app import app
from strawberry.utils.schema_diff import find_breaking_changes_between_sdls


@app.command(help="Compare two GraphQL SDL files for breaking schema changes")
def schema_diff(
    old_schema: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Baseline schema file (for example production SDL)",
    ),
    new_schema: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Candidate schema file to compare against the baseline",
    ),
) -> None:
    try:
        old_text = old_schema.read_text(encoding="utf-8")
        new_text = new_schema.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        rich.print(
            f"[red]Error reading schema files: {rich.markup.escape(str(exc))}[/red]"
        )
        raise typer.Exit(2) from exc

    try:
        changes = find_breaking_changes_between_sdls(old_text, new_text)
    except GraphQLError as exc:
        rich.print(f"[red]Error: {rich.markup.escape(str(exc))}[/red]")
        raise typer.Exit(2) from exc

    if not changes:
        typer.echo("No breaking changes found.")
        return

    for change in changes:
        change_type = getattr(change.type, "name", str(change.type))
        rich.print(
            f"[yellow]{rich.markup.escape(change_type)}:[/yellow]"
            f" {rich.markup.escape(change.description)}"
        )

    raise typer.Exit(1)

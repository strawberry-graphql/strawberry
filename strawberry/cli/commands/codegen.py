from __future__ import annotations

import functools
import importlib
import inspect
from pathlib import Path  # noqa: TC003
from typing import Optional, Union, cast

import rich
import typer

from strawberry.cli.app import app
from strawberry.cli.utils import load_schema
from strawberry.codegen import ConsolePlugin, QueryCodegen, QueryCodegenPlugin


def _is_codegen_plugin(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, (QueryCodegenPlugin, ConsolePlugin))
        and obj is not QueryCodegenPlugin
    )


def _import_plugin(plugin: str) -> Optional[type[QueryCodegenPlugin]]:
    module_name = plugin
    symbol_name: Optional[str] = None

    if ":" in plugin:
        module_name, symbol_name = plugin.split(":", 1)

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None

    if symbol_name:
        obj = getattr(module, symbol_name)

        assert _is_codegen_plugin(obj)
        return obj

    symbols = {
        key: value for key, value in module.__dict__.items() if not key.startswith("__")
    }

    if "__all__" in module.__dict__:
        symbols = {
            name: symbol
            for name, symbol in symbols.items()
            if name in module.__dict__["__all__"]
        }

    for obj in symbols.values():
        if _is_codegen_plugin(obj):
            return obj

    return None


@functools.lru_cache
def _load_plugin(
    plugin_path: str,
) -> type[Union[QueryCodegenPlugin, ConsolePlugin]]:
    # try to import plugin_name from current folder
    # then try to import from strawberry.codegen.plugins

    plugin = _import_plugin(plugin_path)

    if plugin is None and "." not in plugin_path:
        plugin = _import_plugin(f"strawberry.codegen.plugins.{plugin_path}")

    if plugin is None:
        rich.print(f"[red]Error: Plugin {plugin_path} not found")
        raise typer.Exit(1)

    return plugin


def _load_plugins(
    plugin_ids: list[str], query: Path
) -> list[Union[QueryCodegenPlugin, ConsolePlugin]]:
    plugins = []
    for ptype_id in plugin_ids:
        ptype = _load_plugin(ptype_id)
        plugin = ptype(query)
        plugins.append(plugin)

    return plugins


@app.command(help="Generate code from a query")
def codegen(
    query: Optional[list[Path]] = typer.Argument(
        default=None, exists=True, dir_okay=False
    ),
    schema: str = typer.Option(..., help="Python path to the schema file"),
    app_dir: str = typer.Option(
        ".",
        "--app-dir",
        show_default=True,
        help=(
            "Look for the module in the specified directory, by adding this to the "
            "PYTHONPATH. Defaults to the current working directory. "
            "Works the same as `--app-dir` in uvicorn."
        ),
    ),
    output_dir: Path = typer.Option(
        ...,
        "-o",
        "--output-dir",
        exists=True,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
    selected_plugins: list[str] = typer.Option(
        ...,
        "-p",
        "--plugins",
    ),
    cli_plugin: Optional[str] = None,
) -> None:
    if not query:
        return

    schema_symbol = load_schema(schema, app_dir)

    console_plugin_type = _load_plugin(cli_plugin) if cli_plugin else ConsolePlugin
    console_plugin = console_plugin_type(output_dir)
    assert isinstance(console_plugin, ConsolePlugin)
    console_plugin.before_any_start()

    for q in query:
        plugins = cast(list[QueryCodegenPlugin], _load_plugins(selected_plugins, q))

        code_generator = QueryCodegen(
            schema_symbol, plugins=plugins, console_plugin=console_plugin
        )
        code_generator.run(q.read_text())

    console_plugin.after_all_finished()

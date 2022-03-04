import importlib
import inspect
import sys
from typing import List, Optional, Type

import click

from strawberry.cli.utils import load_schema
from strawberry.codegen import QueryCodegen, QueryCodegenPlugin


def _is_codegen_plugin(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, QueryCodegenPlugin)
        and obj is not QueryCodegenPlugin
    )


def _import_plugin(plugin: str) -> Optional[Type[QueryCodegenPlugin]]:
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
    else:
        symbols = {
            key: value
            for key, value in module.__dict__.items()
            if not key.startswith("__")
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


def _load_plugin(plugin_path: str) -> Type[QueryCodegenPlugin]:
    # try to import plugin_name from current folder
    # then try to import from strawberry.codegen.plugins

    plugin = _import_plugin(plugin_path)

    if plugin is None and "." not in plugin_path:
        plugin = _import_plugin(f"strawberry.codegen.plugins.{plugin_path}")

    if plugin is None:
        raise click.ClickException(f"Plugin {plugin_path} not found")

    return plugin


def _load_plugins(plugins: List[str]) -> List[QueryCodegenPlugin]:
    return [_load_plugin(plugin)() for plugin in plugins]


@click.command(short_help="Generate code from a query")
@click.option("--plugin", "-p", multiple=True)
@click.option("--output-dir", "-o", default=".", help="Output directory")
@click.option("--schema", type=str, required=True)
@click.argument("query", type=str)
@click.option(
    "--app-dir",
    default=".",
    type=str,
    show_default=True,
    help=(
        "Look for the module in the specified directory, by adding this to the "
        "PYTHONPATH. Defaults to the current working directory. "
        "Works the same as `--app-dir` in uvicorn."
    ),
)
def codegen(schema: str, query: str, app_dir: str, output_dir: str, plugin: List[str]):
    click.echo(
        click.style(
            "The codegen is experimental. Please submit any bug at "
            "https://github.com/strawberry-graphql/strawberry\n",
            fg="yellow",
            bold=True,
        )
    )

    schema_symbol = load_schema(schema, app_dir)

    sys.path.insert(0, app_dir)

    plugins = _load_plugins(plugin)

    click.echo(
        click.style(
            f"Generating code for {query} using {', '.join(plugin)} plugin(s)",
            fg="green",
        )
    )

    code_generator = QueryCodegen(schema_symbol, plugins=plugins)

    with open(query) as f:
        result = code_generator.codegen(f.read())

    for file in result.files:
        with open(f"{output_dir}/{file.path}", "w") as f:
            f.write(file.content)

    click.echo(
        click.style(f"Generated {len(result.files)} files in {output_dir}", fg="green")
    )

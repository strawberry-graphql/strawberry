import importlib
import inspect
import sys
from typing import List, Optional

import click

from strawberry.cli.utils import load_schema
from strawberry.codegen import CodegenPlugin, QueryCodegen


def _is_codegen_plugin(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, CodegenPlugin)
        and obj is not CodegenPlugin
    )


def _import_plugin(plugin: str) -> Optional[CodegenPlugin]:
    module_name = plugin
    symbol_name: Optional[str] = None

    if ":" in plugin:
        module_name, symbol_name = plugin.split(":", 1)

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None

    if symbol_name:
        plugin = getattr(module, symbol_name)

        if plugin:
            assert isinstance(plugin, CodegenPlugin)
            return plugin
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


def _load_plugin(plugin_path: str) -> CodegenPlugin:
    # try to import plugin_name from current folder
    # then try to import from strawberry.codegen.plugins

    plugin = _import_plugin(plugin_path)

    if plugin is None and "." not in plugin_path:
        plugin = _import_plugin(f"strawberry.codegen.plugins.{plugin_path}")

    if plugin is None:
        raise click.ClickException(f"Plugin {plugin_path} not found")

    return plugin


def _load_plugins(plugins: List[str]) -> List[CodegenPlugin]:
    return [_load_plugin(plugin)() for plugin in plugins]


@click.command(short_help="Generate code from a query")
@click.option("--plugin", "-p", multiple=True)
@click.argument("schema", type=str)
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
def codegen(schema: str, query: str, app_dir: str, plugin: List[str]):
    schema_symbol = load_schema(schema, app_dir)

    sys.path.insert(0, app_dir)

    code_generator = QueryCodegen(schema_symbol, plugins=_load_plugins(plugin))

    with open(query) as f:
        code = code_generator.codegen(f.read())

    print(code)

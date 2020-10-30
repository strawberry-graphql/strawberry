"""
### SDL Importer
Handles argument:

    * input checking
    * import extraction
    * ast conversion preparation
"""
from strawberry.cli.commands.schema_importer import ast_converter, sdl_transpiler


def import_sdl(sdl: str) -> str:
    """
    Determine if filepath or string input.
    Read in or use directly, respectively.
    Look for imports, read those in as well.
    Pass the whole thing to ast_converter.
    """
    ast = ast_converter.convert_to_ast(sdl)
    templates = set({})
    for d in ast.definitions:
        # Parse and render specific ast definitions
        templates.add(sdl_transpiler.transpile(d))

    strawberries = "\n\n".join(templates)
    imports = "import strawberry\n"
    imports += "import typing\n\n\n" if "typing" in strawberries else "\n\n"

    strawberries = imports + strawberries

    return strawberries


def file_to_string(path: str) -> str:
    """ Reads path and returns SDL string """
    with open(path, "r") as f:
        string = f.read()

    return string

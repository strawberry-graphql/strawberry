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

    strawberry_code_template = "\n\n".join(templates)
    imports = (
        "from enum import Enum\n\n" if "(Enum)" in strawberry_code_template else ""
    )
    imports += (
        "from strawberry.directive import DirectiveLocation\n\n"
        if "DirectiveLocation" in strawberry_code_template
        else ""
    )
    imports += "import typing\n\n" if "typing." in strawberry_code_template else ""
    imports += (
        "from typing import Union\n\n" if "Union[" in strawberry_code_template else ""
    )
    imports += "import strawberry\n\n\n"

    strawberry_code_template = imports + strawberry_code_template

    return strawberry_code_template


def file_to_string(path: str) -> str:
    """Reads path and returns SDL string"""
    with open(path, "r") as f:
        string = f.read()

    return string

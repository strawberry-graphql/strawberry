"""
### SDL Importer
Handles argument:

    * input checking
    * import extraction
    * ast conversion preparation
"""
from strawberry.cli.commands.schema_importer import ast_converter, sdl_transpiler


def import_sdl(sdl: str) -> str:  # TODO: Perhaps, transform_sdl_to_code?
    """
    Determine if filepath or string input.
    Read in or use directly, respectively.
    Look for imports, read those in as well.
    Pass the whole thing to ast_converter.
    """
    ast = ast_converter.convert_to_ast(sdl)
    templates = set({})
    for definition in ast.definitions:
        # Parse and render specific ast definitions
        templates.add(sdl_transpiler.transpile(definition))

    strawberry_code_template = "\n\n".join(templates)

    imports = []

    if "(Enum)" in strawberry_code_template:
        imports.append("from enum import Enum")

    if "typing." in strawberry_code_template:
        imports.append("import typing")

    if "Union[" in strawberry_code_template:
        imports.append("from typing import Union")

    if "DirectiveLocation" in strawberry_code_template: 
        imports.append("from strawberry.directive import DirectiveLocation")


    imports.append("import strawberry")  # Append last because it's a third party package

    imports_string = '\n\n'.join(imports)

    code = f"{imports_string}\n\n\n{strawberry_code_template}\n"
    return code


def file_to_string(path: str) -> str:
    """Reads path and returns SDL string"""
    with open(path, "r") as f:
        string = f.read()

    return string

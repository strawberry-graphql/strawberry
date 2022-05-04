"""
### SDL Importer
Handles argument:

    * input checking
    * import extraction
    * ast conversion preparation
"""
from graphql import DefinitionNode
from strawberry.cli.commands.schema_importer import ast_converter, sdl_transpiler


def definition_order(ast_definition: DefinitionNode):
    order = {
        'union_type_definition': 2,
        'enum_type_definition': 1,
    }    
    return order.get(ast_definition.kind, 0)



def import_sdl(sdl: str) -> str:  # TODO: Perhaps, transform_sdl_to_code?
    """
    Determine if filepath or string input.
    Read in or use directly, respectively.
    Look for imports, read those in as well.
    Pass the whole thing to ast_converter.
    """
    ast = ast_converter.convert_to_ast(sdl)
    # Sort definitions to generate code for unions or enums when all references have been resolved.
    ordered_definitions = sorted(ast.definitions, key=definition_order)
    strawberry_code = "\n\n".join(map(sdl_transpiler.transpile, ordered_definitions))

    imports = []
    if "(Enum)" in strawberry_code:
        imports.append("from enum import Enum")

    if "typing." in strawberry_code:
        imports.append("import typing")

    if "Union[" in strawberry_code:
        imports.append("from typing import Union")

    if "DirectiveLocation" in strawberry_code:
        imports.append("from strawberry.directive import DirectiveLocation")

    imports.append(
        "import strawberry"  # Append last because it's a third party package
    )

    imports_string = "\n\n".join(imports)

    code = f"{imports_string}\n\n\n{strawberry_code}\n"
    return code


def file_to_string(path: str) -> str:
    """Reads path and returns SDL string"""
    with open(path, "r") as f:
        string = f.read()

    return string

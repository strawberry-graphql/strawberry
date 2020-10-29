import os
import re

from graphql.language import parse
from graphql.error import GraphQLError

from strawberry.cli.commands.schema_importer import ast_converter, sdl_transpiler

GQL_IMPORT_REGEX = r"#import \"(.*\.gql|.*\.graphql)\""


def import_sdl(sdl: str) -> str:
    """
    Determine if filepath or string input.
    Read in or use directly, respectively.
    Look for imports, read those in as well.
    Pass the whole thing to ast_converter.
    """
    sdl_strings = []

    if os.path.exists(sdl):
        root = file_to_string(sdl)
    # ?: else if: try and download __schema
    # from existing server with provided url?
    else:
        root = sdl

    imports = get_imports(root)

    for i in imports:
        try:
            s = file_to_string(i)
            sdl_strings.append(remove_import_statements(s))

        except FileNotFoundError as e:
            print(f"File not found on path: {i}")
            continue

        except GraphQLError as e:
            print(f"A file contains syntax errors {i}")
            continue

    sdl_strings.append(root)
    ast = ast_converter.convert_to_ast("\n".join(sdl_strings))
    templates = set({})
    for d in ast.definitions:
        # Parse and render specific ast definitions
        templates.add(sdl_transpiler.transpile(d))

    strawberries = "\n\n".join(templates)
    imports = "import strawberry"
    imports += "\nimport typing\n\n" if "typing" in strawberries else ""

    strawberries = imports + strawberries

    return strawberries


def get_imports(sdl: str, imports: set = set({})) -> set:
    """
    Recursively probe files for import statements.
    Add new statements to a set, implicitly removing duplicates.
    """
    matches = re.findall(GQL_IMPORT_REGEX, sdl)
    for m in matches:
        imports.add(m)
        try:
            get_imports(file_to_string(m), imports)
        except FileNotFoundError as e:
            print(f"File not found on path: {m}")
            continue

    return imports


def file_to_string(path: str) -> str:
    """ Reads path and returns SDL string """
    with open(path, "r") as f:
        string = f.read()

    return string


def remove_import_statements(string: str) -> str:
    """ Removes import statements from strings """
    string = re.sub(GQL_IMPORT_REGEX, "", string)
    string = re.sub("\n", "", string)
    return string

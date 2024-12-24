import textwrap
from inspect import iscoroutinefunction
from typing import Optional
from typing_extensions import Protocol

from graphql import (
    DocumentNode,
    FieldNode,
    IntValueNode,
    OperationDefinitionNode,
    SelectionSetNode,
    StringValueNode,
)
from graphql.language import OperationType
from graphql.language.parser import parse

from strawberry.scalars import is_scalar
from strawberry.schema import Schema
from strawberry.types.base import (
    StrawberryList,
    StrawberryObjectDefinition,
    StrawberryOptional,
    StrawberryType,
    get_object_definition,
)
from strawberry.types.union import StrawberryUnion


class HasSelectionSet(Protocol):
    selection_set: Optional[SelectionSetNode]


def _recurse(
    definition: HasSelectionSet,
    root_type: StrawberryType,
    schema: Schema,
    level: int = 0,
    indent: int = 1,
    path: str = "Query",
    root_value_variable: str = "root_value",
) -> str:
    body = []

    if hasattr(root_type, "__strawberry_definition__"):
        root_type = root_type.__strawberry_definition__

    # TODO: results can be list or dict or None

    if isinstance(root_type, StrawberryList):
        result = "[]"
        body.append(f"results_{level} = {result}")
        body.append("for item in value:")

        of_type = root_type.of_type

        body.append(
            _recurse(
                definition,
                of_type,
                level=level + 1,
                indent=1,
                path=path,
                schema=schema,
                root_value_variable="item",
            )
        )

        # TODO: I HATE THIS :'D
        body.append(f"    results_{level}.append(results_{level+1})")
        body.append(f"results_{level-1}['{definition.name.value}'] = results_{level}")
        body.append("")

    elif isinstance(root_type, StrawberryOptional):
        body.append(
            _recurse(
                definition, root_type.of_type, level=level, indent=0, schema=schema
            )
        )

    elif isinstance(root_type, StrawberryUnion):
        body.append("# TODO: unions")

    elif isinstance(root_type, StrawberryObjectDefinition):
        result = "{}"
        body.append(f"results_{level} = {result}")

        root_value = root_value_variable
        info_value = "None"

        body.append(f"root_type_{level} = {root_type.name}.__strawberry_definition__")
        body.append(f"# {path}")

        if not definition.selection_set:
            raise ValueError("This shouldn't happen")

        for selection in definition.selection_set.selections:
            body.append(f"# {path}.{selection.name.value}")
            assert isinstance(selection, FieldNode)

            # get arguments

            arguments = {}

            for argument in selection.arguments:
                if isinstance(argument.value, (StringValueNode, IntValueNode)):
                    arguments[argument.name.value] = argument.value.value
                else:
                    raise NotImplementedError(
                        f"Argument {argument.value} not supported"
                    )

            field_name = selection.name.value

            field = next(
                field for field in root_type.fields if field.name == field_name
            )

            index = root_type.fields.index(field)
            resolver = field._resolver

            body.append(f"field = root_type_{level}.fields[{index}]")

            # append arguments
            body.append(f"arguments = {arguments}")

            if iscoroutinefunction(resolver):
                body.append(
                    f"value = await field._resolver({root_value}, {info_value}, **arguments)"
                )
            else:
                if field.is_basic_field:
                    body.append(f"value = {root_value}.{field_name}")
                else:
                    body.append(
                        f"value = field._resolver({root_value}, {info_value}, **arguments)"
                    )

            body.append(
                _recurse(
                    selection,
                    field.type,
                    level=level + 1,
                    indent=0,
                    path=f"{path}.{field_name}",
                    schema=schema,
                )
            )

    elif is_scalar(root_type, schema.schema_converter.scalar_registry):
        body.append(f"results_{level - 1}['{definition.name.value}'] = value")

    else:
        raise NotImplementedError(f"Type {root_type} not supported")

    return textwrap.indent("\n".join(body), "    " * indent)


def compile(operation: str, schema: Schema) -> ...:
    # TODO::
    # 1. Parse the operation
    # 2. For each field in the operation, get the type of the field
    # 3. Get the fields of the type

    ast = parse(operation)

    assert isinstance(ast, DocumentNode)

    # assuming only one definition (for now)

    definition = ast.definitions[0]

    assert isinstance(definition, OperationDefinitionNode)

    # TODO: this is an assumption, but we go with query for now
    # Mutations and subscriptions are also possible, but they need to be handled differently
    # mutation are serial, subscriptions are more complex

    assert definition.operation == OperationType.QUERY

    root_type = get_object_definition(schema.query, strict=True)

    # TODO: we might want to think about root values too

    function = textwrap.dedent(
        """
        # TODO: variables
        async def _compiled_operation(schema, root_value):
        __BODY__
            return results_0
        """
    )

    function = function.replace(
        "__BODY__", _recurse(definition, root_type, schema=schema)
    )

    return function

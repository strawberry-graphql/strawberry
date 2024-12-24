import textwrap
from inspect import iscoroutinefunction
from typing import List, Optional, Tuple
from typing_extensions import Protocol

from graphql import (
    ArgumentNode,
    DocumentNode,
    FieldNode,
    IntValueNode,
    OperationDefinitionNode,
    SelectionSetNode,
    StringValueNode,
    VariableNode,
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


def _get_arguments(arguments: Tuple[ArgumentNode, ...]) -> List[str]:
    body = []

    body.append("arguments = {}")

    for argument in arguments:
        if isinstance(argument.value, StringValueNode):
            body.append(
                f"arguments['{argument.name.value}'] = '{argument.value.value}'"
            )
        if isinstance(argument.value, IntValueNode):
            body.append(f"arguments['{argument.name.value}'] = {argument.value.value}")
        elif isinstance(argument.value, VariableNode):
            body.append(
                f"arguments['{argument.name.value}'] = variables['{argument.value.name.value}']"
            )
        else:
            raise NotImplementedError(f"Argument {argument.value} not supported")

    return body


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

    body.append(f"# root_value_variable: {root_value_variable}")
    if hasattr(root_type, "__strawberry_definition__"):
        root_type = root_type.__strawberry_definition__

    # TODO: results can be list or dict or None

    if isinstance(root_type, StrawberryList):
        result = "[]"
        body.append(f"results_{level} = {result}")
        body.append(f"for item in value_{level - 1}:")

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
        body.append(f"# Object: {root_type.name}")
        result = "{}"
        body.append(f"results_{level} = {result}")

        info_value = "None"

        body.append(f"root_type_{level} = {root_type.name}.__strawberry_definition__")
        body.append(f"# {path}")

        if not definition.selection_set:
            raise ValueError("This shouldn't happen")

        for selection in definition.selection_set.selections:
            body.append(f"# {path}.{selection.name.value}")
            assert isinstance(selection, FieldNode)

            # get arguments
            body.extend(_get_arguments(selection.arguments))

            field_name = selection.name.value

            field = next(
                field for field in root_type.fields if field.name == field_name
            )

            index = root_type.fields.index(field)
            resolver = field._resolver

            body.append(f"field = root_type_{level}.fields[{index}]")

            # append arguments
            if iscoroutinefunction(resolver):
                body.append(
                    f"value_{level} = await field._resolver({root_value_variable}, {info_value}, **arguments)"
                )
            else:
                if field.is_basic_field:
                    body.append(f"value_{level} = {root_value_variable}.{field_name}")
                else:
                    body.append(
                        f"value_{level} = field._resolver({root_value_variable}, {info_value}, **arguments)"
                    )

            body.append(
                _recurse(
                    selection,
                    field.type,
                    root_value_variable=f"value_{level}",
                    level=level + 1,
                    indent=0,
                    path=f"{path}.{field_name}",
                    schema=schema,
                )
            )

        # TODO: this is wrong?
        # test with more nesting :')
        if level > 2:
            body.append(
                f"results_{level - 1}['{definition.name.value}'] = results_{level}"
            )

    elif is_scalar(root_type, schema.schema_converter.scalar_registry):
        body.append(
            f"results_{level - 1}['{definition.name.value}'] = value_{level - 1}"
        )

    else:
        raise NotImplementedError(f"Type {root_type} not supported")

    return textwrap.indent("\n".join(body), "    " * indent)


def compile(operation: str, schema: Schema) -> ...:
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
        async def _compiled_operation(schema, root_value, variables):
        __BODY__
            return results_0
        """
    )

    function = function.replace(
        "__BODY__", _recurse(definition, root_type, schema=schema)
    )

    return function

import textwrap
from functools import lru_cache

from graphql import DocumentNode, FieldNode, OperationDefinitionNode
from graphql.language import OperationType
from graphql.language.parser import parse

from strawberry.schema import Schema
from strawberry.types.base import StrawberryList, get_object_definition

memoised_parse = lru_cache(maxsize=None)(parse)


def _recurse(definition, root_type) -> str:
    body_lines = []

    body_lines.append("root_type_definition = Query.__strawberry_definition__")
    body_lines.append("results = {}")
    body_lines.append("")

    # for async stuff we can use asyncio.gather or, better, tasks groups
    # we can say that the JIT only works on 3.x (whatever has task groups)?

    # TODO: add comments to code

    # we need to handle fragments and other stuff
    for selection in definition.selection_set.selections:
        assert isinstance(selection, FieldNode)

        field_name = selection.name.value
        root_field_name = field_name

        # TODO: we need a way to get the field from the GraphQL name
        field = root_type.get_field(field_name)

        assert field

        return_type = field.type

        # TODO: we need to check if this is async or now, assumption that it is for now
        # TODO: we also need to check if we need to pass async
        # but all of this will be a function, so there's not going to be much penalty
        # but we need to build the info object :'D

        if isinstance(return_type, StrawberryList):
            body_lines.append(f"{field_name} = []")
            of_type = return_type.of_type
            of_type_definition = get_object_definition(of_type, strict=True)

            type_name = of_type_definition.name

            # TODO: here we can find the actual implementation of the field
            # and import it, for now we'll go the schema route
            body_lines.append(f"field_type = schema.get_type_by_name('{type_name}')")
            # TODO: we can find this once, or use a map, but we also need to find the
            # python name (we are working with the GraphQL name)
            body_lines.append(
                f"current_field = next(field for field in root_type_definition.fields if field.name == '{field_name}')"
            )
            # TODO: this could be a good place to check if the field is async
            # `_resolver` is added by me in the schema converted
            body_lines.append(
                "field_results = await current_field._resolver(None, None)"
            )
            body_lines.append("")

            body_lines.append("current_type = field_type")
            body_lines.append("current_field_results = []")
            body_lines.append("for item in field_results:")
            # TODO: this should be the place to recurse
            body_lines.append("    item_result = {}")
            body_lines.append("")

            for sub_selection in selection.selection_set.selections:
                assert isinstance(sub_selection, FieldNode)

                field_name = sub_selection.name.value

                field = next(
                    field
                    for field in of_type_definition.fields
                    if field.name == field_name
                )

                index = of_type_definition.fields.index(field)

                # TODO: for now find the index
                body_lines.append(f"    field = field_type.fields[{index}]")

                body_lines.append(
                    f"    item_result['{field_name}'] = field._resolver(item, None)"
                )

                body_lines.append("")

            body_lines.append("    current_field_results.append(item_result)")
            body_lines.append("")
            body_lines.append(f"results['{root_field_name}'] = current_field_results")

    return textwrap.indent("\n".join(body_lines), " " * 4)


def compile(operation: str, schema: Schema) -> ...:
    # TODO::
    # 1. Parse the operation
    # 2. For each field in the operation, get the type of the field
    # 3. Get the fields of the type

    ast = memoised_parse(operation)

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
            return results
        """
    )

    function = function.replace("__BODY__", _recurse(definition, root_type))

    return function

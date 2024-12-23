from functools import lru_cache

from graphql import DocumentNode, FieldNode, OperationDefinitionNode
from graphql.language import OperationType
from graphql.language.parser import parse

from strawberry.schema import Schema
from strawberry.types.base import StrawberryList, get_object_definition

memoised_parse = lru_cache(maxsize=None)(parse)


async def compile(operation: str, schema: Schema) -> ...:
    # TODO::
    # 1. Parse the operation
    # 2. For each field in the operation, get the type of the field
    # 3. Get the fields of the type

    ast = memoised_parse(operation)

    print(ast)

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

    results = {}

    # THIS might become recursive, might need to handle fragments and other stuff
    for selection in definition.selection_set.selections:
        assert isinstance(selection, FieldNode)

        field_name = selection.name.value

        # TODO: we need a way to get the field from the GraphQL name
        field = root_type.get_field(field_name)

        assert field

        return_type = field.type

        # TODO: we need to check if this is async or now, assumption that it is for now
        # TODO: we also need to check if we need to pass async
        # but all of this will be a function, so there's not going to be much penalty
        # but we need to build the info object :'D

        field_results = await field._resolver(None, None)

        if isinstance(return_type, StrawberryList):
            of_type = return_type.of_type
            of_type_definition = get_object_definition(of_type, strict=True)

            compiled_field_results = []

            for item in field_results:
                # TODO: assumptions: we are only fetching basic fields
                item_result = {}

                for sub_selection in selection.selection_set.selections:
                    assert isinstance(sub_selection, FieldNode)

                    sub_field_name = sub_selection.name.value

                    # TODO: memoize this
                    sub_field = of_type_definition.get_field(sub_field_name)

                    assert sub_field

                    sub_field_results = sub_field._resolver(item, None)

                    item_result[sub_field_name] = sub_field_results

                compiled_field_results.append(item_result)

        # `_resolver` is added by me in the schema converted

        results[field_name] = compiled_field_results

    return results

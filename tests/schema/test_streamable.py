import textwrap

import strawberry
from strawberry.type import StrawberryList, get_object_definition


def test_streamable_field():
    @strawberry.type
    class Query:
        @strawberry.field
        async def posts() -> strawberry.Streamable[str]:
            yield "🔥"

    definition = get_object_definition(Query, strict=True)

    assert definition.name == "Query"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "posts"
    assert definition.fields[0].graphql_name is None

    assert isinstance(definition.fields[0].type, StrawberryList)
    assert definition.fields[0].type.of_type == str

    schema = strawberry.Schema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Query {
          posts: [String!]!
        }
        """
    ).strip()

    assert str(schema) == expected_schema

import textwrap

import strawberry
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.field import StrawberryField


def test_can_change_which_fields_are_exposed():
    @strawberry.type
    class User:
        name: str
        email: str = strawberry.field(metadata={"tags": ["internal"]})

    @strawberry.type
    class Query:
        user: User

    def public_field_filter(field: StrawberryField) -> bool:
        return "internal" not in field.metadata.get("tags", [])

    class PublicSchema(strawberry.Schema):
        def get_fields(
            self, type_definition: StrawberryObjectDefinition
        ) -> list[StrawberryField]:
            fields = super().get_fields(type_definition)
            return list(filter(public_field_filter, fields))

    schema = PublicSchema(query=Query)

    expected_schema = textwrap.dedent(
        """
        type Query {
          user: User!
        }

        type User {
          name: String!
        }
        """
    ).strip()

    assert schema.as_str() == expected_schema

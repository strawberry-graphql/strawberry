# type: ignore

import textwrap

import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location


def test_additional_schema_directives_printed_correctly_object():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class CacheControl:
        max_age: int

    @strawberry.federation.type(
        keys=["id"], shareable=True, extend=True, directives=[CacheControl(max_age=42)]
    )
    class FederatedType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        federatedType: FederatedType

    expected_type = """
    directive @CacheControl(max_age: Int!) on OBJECT

    extend type FederatedType @CacheControl(max_age: 42) @key(fields: "id") @shareable {
      id: ID!
    }

    type Query {
      federatedType: FederatedType!
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )
    assert schema.as_str() == textwrap.dedent(expected_type).strip()


def test_additional_schema_directives_printed_in_order_object():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class CacheControl0:
        max_age: int

    @strawberry.schema_directive(locations=[Location.OBJECT])
    class CacheControl1:
        min_age: int

    @strawberry.federation.type(
        keys=["id"],
        shareable=True,
        extend=True,
        directives=[CacheControl0(max_age=42), CacheControl1(min_age=42)],
    )
    class FederatedType:
        id: strawberry.ID

    @strawberry.type
    class Query:
        federatedType: FederatedType

    expected_type = """
    directive @CacheControl0(max_age: Int!) on OBJECT

    directive @CacheControl1(min_age: Int!) on OBJECT

    extend type FederatedType @CacheControl0(max_age: 42) @CacheControl1(min_age: 42) @key(fields: "id") @shareable {
      id: ID!
    }

    type Query {
      federatedType: FederatedType!
    }
    """

    schema = strawberry.Schema(
        query=Query, config=StrawberryConfig(auto_camel_case=False)
    )
    assert schema.as_str() == textwrap.dedent(expected_type).strip()

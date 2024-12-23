import textwrap
from enum import Enum
from typing import Annotated, Union

import strawberry


def test_field_tag_printed_correctly():
    @strawberry.federation.interface(tags=["myTag", "anotherTag"])
    class SomeInterface:
        id: strawberry.ID

    @strawberry.federation.type(tags=["myTag", "anotherTag"])
    class Product(SomeInterface):
        upc: str = strawberry.federation.field(
            external=True, tags=["myTag", "anotherTag"]
        )

    @strawberry.federation.type
    class Query:
        @strawberry.field
        def top_products(
            self, first: Annotated[int, strawberry.federation.argument(tags=["myTag"])]
        ) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@external", "@tag"]) {
          query: Query
        }

        type Product implements SomeInterface @tag(name: "myTag") @tag(name: "anotherTag") {
          id: ID!
          upc: String! @external @tag(name: "myTag") @tag(name: "anotherTag")
        }

        type Query {
          _service: _Service!
          topProducts(first: Int! @tag(name: "myTag")): [Product!]!
        }

        interface SomeInterface @tag(name: "myTag") @tag(name: "anotherTag") {
          id: ID!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_scalar():
    @strawberry.federation.scalar(tags=["myTag", "anotherTag"])
    class SomeScalar(str):
        __slots__ = ()

    @strawberry.federation.type
    class Query:
        hello: SomeScalar

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeScalar!
        }

        scalar SomeScalar @tag(name: "myTag") @tag(name: "anotherTag")

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_enum():
    @strawberry.federation.enum(tags=["myTag", "anotherTag"])
    class SomeEnum(Enum):
        A = "A"

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum @tag(name: "myTag") @tag(name: "anotherTag") {
          A
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_enum_value():
    @strawberry.enum
    class SomeEnum(Enum):
        A = strawberry.federation.enum_value("A", tags=["myTag", "anotherTag"])

    @strawberry.federation.type
    class Query:
        hello: SomeEnum

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        type Query {
          _service: _Service!
          hello: SomeEnum!
        }

        enum SomeEnum {
          A @tag(name: "myTag") @tag(name: "anotherTag")
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_field_tag_printed_correctly_on_union():
    @strawberry.type
    class A:
        a: str

    @strawberry.type
    class B:
        b: str

    MyUnion = Annotated[
        Union[A, B], strawberry.federation.union("Union", tags=["myTag", "anotherTag"])
    ]

    @strawberry.federation.type
    class Query:
        hello: MyUnion

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        type A {
          a: String!
        }

        type B {
          b: String!
        }

        type Query {
          _service: _Service!
          hello: Union!
        }

        union Union @tag(name: "myTag") @tag(name: "anotherTag") = A | B

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()


def test_tag_printed_correctly_on_inputs():
    @strawberry.federation.input(tags=["myTag", "anotherTag"])
    class Input:
        a: str = strawberry.federation.field(tags=["myTag", "anotherTag"])

    @strawberry.federation.type
    class Query:
        hello: str

    schema = strawberry.federation.Schema(
        query=Query, types=[Input], enable_federation_2=True
    )

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@tag"]) {
          query: Query
        }

        input Input @tag(name: "myTag") @tag(name: "anotherTag") {
          a: String! @tag(name: "myTag") @tag(name: "anotherTag")
        }

        type Query {
          _service: _Service!
          hello: String!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert schema.as_str() == textwrap.dedent(expected).strip()

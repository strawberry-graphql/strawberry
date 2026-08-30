import textwrap
import warnings
from typing import Generic, NewType, TypeVar

import pytest
from graphql import build_schema

import strawberry
from strawberry.federation.types import FieldSet, LinkImport, LinkPurpose
from strawberry.schema_directive import Location


def test_entities_type_when_no_type_has_keys():
    @strawberry.federation.type()
    class Product:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected_sdl = textwrap.dedent("""
        type Product {
          upc: String!
          name: String
          price: Int
          weight: Int
        }

        extend type Query {
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """).strip()

    assert str(schema) == expected_sdl

    query = """
        query {
            __type(name: "_Entity") {
                kind
                possibleTypes {
                    name
                }
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": None}


def test_entities_type():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    expected_sdl = textwrap.dedent("""
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @key(fields: "upc") {
          upc: String!
          name: String
          price: Int
          weight: Int
        }

        extend type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """).strip()

    assert str(schema) == expected_sdl

    query = """
        query {
            __type(name: "_Entity") {
                kind
                possibleTypes {
                    name
                }
            }
            fieldSet: __type(name: "_FieldSet") {
                kind
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {
        "__type": {"kind": "UNION", "possibleTypes": [{"name": "Product"}]},
        "fieldSet": {"kind": "SCALAR", "name": "_FieldSet"},
    }


def test_runtime_registration_opt_out_does_not_hide_federation_directives():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class RuntimeOptOut:
        __strawberry_register_definition__ = False

    @strawberry.federation.type(keys=["upc"], directives=[RuntimeOptOut()])
    class Product:
        upc: str

    @strawberry.type
    class Query:
        product: Product

    schema = strawberry.federation.Schema(query=Query)

    assert schema._schema.get_directive("runtimeOptOut") is None
    assert schema._schema.get_directive("key") is not None
    assert schema._schema.get_directive("link") is not None

    expected_sdl = textwrap.dedent("""
        directive @runtimeOptOut on OBJECT

        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @runtimeOptOut @key(fields: "upc") {
          upc: String!
        }

        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
        }

        scalar _Any

        union _Entity = Product

        type _Service {
          sdl: String!
        }
    """).strip()

    sdl = schema.as_str()
    assert sdl == expected_sdl


def test_additional_scalars():
    @strawberry.federation.type(keys=["upc"])
    class Example:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Example]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query {
            __type(name: "_Any") {
                kind
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": {"kind": "SCALAR"}}


def test_user_type_named_like_private_federation_type_is_printed():
    UserFieldSet = NewType("UserFieldSet", str)

    @strawberry.type
    class Query:
        field_set: UserFieldSet

    schema = strawberry.federation.Schema(
        query=Query,
        scalar_overrides={
            UserFieldSet: strawberry.scalar(
                name="_FieldSet",
                serialize=lambda value: value,
                parse_value=str,
            )
        },
    )

    expected_sdl = textwrap.dedent("""
        type Query {
          _service: _Service!
          fieldSet: _FieldSet!
        }

        scalar _Any

        scalar _FieldSet

        type _Service {
          sdl: String!
        }
    """).strip()

    assert schema.as_str() == expected_sdl


def test_private_federation_types_are_printed_when_used_by_fields():
    @strawberry.type
    class Query:
        field_set: FieldSet
        link_import: LinkImport
        link_purpose: LinkPurpose

    schema = strawberry.federation.Schema(query=Query)

    expected_sdl = textwrap.dedent("""
        type Query {
          _service: _Service!
          fieldSet: _FieldSet!
          linkImport: link__Import!
          linkPurpose: link__Purpose!
        }

        scalar _Any

        scalar _FieldSet

        type _Service {
          sdl: String!
        }

        scalar link__Import

        enum link__Purpose {
          SECURITY
          EXECUTION
        }
    """).strip()

    sdl = schema.as_str()
    assert sdl == expected_sdl
    build_schema(sdl)


def test_service():
    @strawberry.federation.type
    class Product:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query {
            _service {
                sdl
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    sdl = """
        type Product {
          upc: String!
        }

        extend type Query {
          _service: _Service!
          topProducts(first: Int!): [Product!]!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert result.data == {"_service": {"sdl": textwrap.dedent(sdl).strip()}}


def test_using_generics():
    T = TypeVar("T")

    @strawberry.federation.type
    class Product:
        upc: str

    @strawberry.type
    class ListOfProducts(Generic[T]):
        products: list[T]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(
            self, first: int
        ) -> ListOfProducts[Product]:  # pragma: no cover
            return ListOfProducts(products=[])

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query {
            _service {
                sdl
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    sdl = """
        type Product {
          upc: String!
        }

        type ProductListOfProducts {
          products: [Product!]!
        }

        extend type Query {
          _service: _Service!
          topProducts(first: Int!): ProductListOfProducts!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert result.data == {"_service": {"sdl": textwrap.dedent(sdl).strip()}}


def test_input_types():
    @strawberry.federation.input(inaccessible=True)
    class ExampleInput:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, example: ExampleInput) -> list[str]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query)

    query = """
        query {
            __type(name: "ExampleInput") {
                kind
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {"__type": {"kind": "INPUT_OBJECT"}}


def test_can_create_schema_without_query():
    @strawberry.federation.type()
    class Product:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    schema = strawberry.federation.Schema(types=[Product])

    assert (
        str(schema)
        == textwrap.dedent(
            """
                type Product {
                  upc: String!
                  name: String
                  price: Int
                  weight: Int
                }

                type Query {
                  _service: _Service!
                }

                scalar _Any

                type _Service {
                  sdl: String!
                }
            """
        ).strip()
    )


def test_federation_schema_warning():
    @strawberry.federation.type(keys=["upc"])
    class ProductFed:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    with pytest.warns(UserWarning) as record:  # noqa: PT030
        strawberry.Schema(
            query=ProductFed,
        )

    assert (
        "Federation directive found in schema. "
        "Use `strawberry.federation.Schema` instead of `strawberry.Schema`."
        in [str(r.message) for r in record]
    )


def test_does_not_warn_when_using_federation_schema():
    @strawberry.federation.type(keys=["upc"])
    class ProductFed:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    @strawberry.type
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[ProductFed]:  # pragma: no cover
            return []

    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message=r"'.*' is deprecated and slated for removal in Python 3\.\d+",
        )

        strawberry.federation.Schema(
            query=Query,
        )

    assert len(w) == 0

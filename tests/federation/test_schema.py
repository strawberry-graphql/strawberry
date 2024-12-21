import textwrap
import warnings
from typing import Generic, Optional, TypeVar

import pytest

import strawberry


def test_entities_type_when_no_type_has_keys():
    @strawberry.federation.type()
    class Product:
        upc: str
        name: Optional[str]
        price: Optional[int]
        weight: Optional[int]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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
        name: Optional[str]
        price: Optional[int]
        weight: Optional[int]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    expected_sdl = textwrap.dedent("""
        schema @link(url: "https://specs.apollo.dev/federation/v2.7", import: ["@key"]) {
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
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.data == {
        "__type": {"kind": "UNION", "possibleTypes": [{"name": "Product"}]}
    }


def test_additional_scalars():
    @strawberry.federation.type(keys=["upc"])
    class Example:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Example]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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


def test_service():
    @strawberry.federation.type
    class Product:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> list[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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
        name: Optional[str]
        price: Optional[int]
        weight: Optional[int]

    schema = strawberry.federation.Schema(types=[Product], enable_federation_2=True)

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
        name: Optional[str]
        price: Optional[int]
        weight: Optional[int]

    with pytest.warns(UserWarning) as record:
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
        name: Optional[str]
        price: Optional[int]
        weight: Optional[int]

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
            enable_federation_2=True,
        )

    assert len(w) == 0

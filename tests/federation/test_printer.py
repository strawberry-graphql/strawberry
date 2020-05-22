import textwrap
import typing

import strawberry
from strawberry.printer import print_schema, print_type


def test_print_extend():
    @strawberry.federation.type(extend=True)
    class Product:
        upc: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    expected_representation = """
        extend type Product {
          upc: String!
          name: String
          price: Int
          weight: Int
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_type_with_key():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    expected_representation = """
        type Product @key(fields: "upc") {
          upc: String!
          name: String
          price: Int
          weight: Int
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_type_with_multiple_keys():
    @strawberry.federation.type(keys=["upc", "sku"])
    class Product:
        upc: str
        sku: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    expected_representation = """
        type Product @key(fields: "upc") @key(fields: "sku") {
          upc: String!
          sku: String!
          name: String
          price: Int
          weight: Int
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_provides():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: typing.Optional[str]

    @strawberry.federation.type(keys=["id"])
    class Review:
        product: Product = strawberry.federation.field(provides="name")

    expected_representation = """
        type Review @key(fields: "id") {
          product: Product! @provides(fields: "name")
        }
    """

    assert print_type(Review) == textwrap.dedent(expected_representation).strip()


def test_print_external():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str = strawberry.federation.field(external=True)
        name: str = strawberry.federation.field(external=True)

    expected_representation = """
        type Product @key(fields: "upc") {
          upc: String! @external
          name: String! @external
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_requires():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        name: str = strawberry.federation.field(requires="email")

    expected_representation = """
        type Product @key(fields: "upc") {
          name: String! @requires(fields: "email")
        }
    """

    assert print_type(Product) == textwrap.dedent(expected_representation).strip()


def test_print_schema():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, info, first: int) -> typing.List[Product]:
            return []

    expected_representation = """
        type Product @key(fields: "upc") {
          upc: String!
          name: String
          price: Int
          weight: Int
        }

        extend type Query {
          topProducts(first: Int!): [Product!]!
        }
    """

    schema = strawberry.Schema(query=Query)

    assert print_schema(schema) == textwrap.dedent(expected_representation).strip()

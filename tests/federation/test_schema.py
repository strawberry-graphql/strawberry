import textwrap
import typing

import strawberry


def test_entities_type_when_no_type_has_keys():
    @strawberry.federation.type()
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

    schema = strawberry.federation.Schema(query=Query)

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
        name: typing.Optional[str]
        price: typing.Optional[int]
        weight: typing.Optional[int]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, info, first: int) -> typing.List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query)

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
        def top_products(self, info, first: int) -> typing.List[Example]:
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


def test_service():
    @strawberry.federation.type
    class Product:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, info, first: int) -> typing.List[Product]:
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

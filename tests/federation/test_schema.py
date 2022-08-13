import textwrap
from typing import Generic, List, Optional, TypeVar

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
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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
        def top_products(self, first: int) -> List[Product]:
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

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
        def top_products(self, first: int) -> List[Example]:
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
        def top_products(self, first: int) -> List[Product]:
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
        products: List[T]

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> ListOfProducts[Product]:
            return ListOfProducts([])

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
        def top_products(self, example: ExampleInput) -> List[str]:
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

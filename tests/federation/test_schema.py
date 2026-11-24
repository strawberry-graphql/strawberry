import textwrap
import warnings
from typing import Generic, NewType, TypeVar

import pytest
from graphql import build_schema

import strawberry
from strawberry.federation.types import FieldSet, LinkImport, LinkPurpose
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.name_converter import HasGraphQLName, NameConverter
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


def test_registers_custom_and_federation_directives():
    @strawberry.schema_directive(locations=[Location.OBJECT])
    class Custom: ...

    @strawberry.federation.type(keys=["upc"], directives=[Custom()])
    class Product:
        upc: str

    @strawberry.type
    class Query:
        product: Product

    schema = strawberry.federation.Schema(query=Query)

    assert schema._schema.get_directive("custom") is not None
    assert schema._schema.get_directive("key") is not None
    assert schema._schema.get_directive("link") is not None

    expected_sdl = textwrap.dedent("""
        directive @custom on OBJECT

        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @custom @key(fields: "upc") {
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


def test_query_fields_named_like_federation_resolvers_are_kept():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

    @strawberry.type
    class Query:
        product: Product

        @strawberry.field
        def service(self) -> str:
            return "service"

        @strawberry.field
        def entities_resolver(self) -> str:
            return "entities"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        schema = strawberry.federation.Schema(query=Query)

    expected = """
        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
          service: String!
          entitiesResolver: String!
        }
    """

    assert textwrap.dedent(expected).strip() in str(schema)

    result = schema.execute_sync("{ service entitiesResolver }")

    assert not result.errors
    assert result.data == {"service": "service", "entitiesResolver": "entities"}


def test_query_fields_with_federation_python_names_are_kept():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

    @strawberry.type
    class Query:
        product: Product

        @strawberry.field(name="serviceInfo")
        def _service(self) -> str:
            return "service"

        @strawberry.field(name="entitiesInfo")
        def _entities(self) -> str:
            return "entities"

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        schema = strawberry.federation.Schema(query=Query)

    expected = """
        type Query {
          _entities(representations: [_Any!]!): [_Entity]!
          _service: _Service!
          product: Product!
          serviceInfo: String!
          entitiesInfo: String!
        }
    """

    assert textwrap.dedent(expected).strip() in str(schema)

    result = schema.execute_sync("{ serviceInfo entitiesInfo }")

    assert not result.errors
    assert result.data == {"serviceInfo": "service", "entitiesInfo": "entities"}


def test_query_can_define_its_own_service_field():
    @strawberry.type(name="_Service")
    class CustomService:
        sdl: str

    @strawberry.type
    class Query:
        hello: str

        @strawberry.field(name="_service")
        def custom_service(self) -> CustomService:
            return CustomService(sdl="custom sdl")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        schema = strawberry.federation.Schema(query=Query)

    result = schema.execute_sync("{ _service { sdl } }")

    assert not result.errors
    assert result.data == {"_service": {"sdl": "custom sdl"}}


def test_query_can_define_its_own_service_and_entities_fields():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

    @strawberry.type(name="_Service")
    class CustomService:
        sdl: str

    @strawberry.type
    class Query:
        product: Product

        @strawberry.field(name="_service")
        def custom_service(self) -> CustomService:
            return CustomService(sdl="custom sdl")

        @strawberry.field(name="_entities")
        def custom_entities(self) -> list[Product]:
            return [Product(id=strawberry.ID("1"))]

    schema = strawberry.federation.Schema(query=Query)

    expected = """
        schema @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@key"]) {
          query: Query
        }

        type Product @key(fields: "id") {
          id: ID!
        }

        type Query {
          product: Product!
          _service: _Service!
          _entities: [Product!]!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    """

    assert str(schema) == textwrap.dedent(expected).strip()

    result = schema.execute_sync("{ _service { sdl } _entities { id } }")

    assert not result.errors
    assert result.data == {
        "_service": {"sdl": "custom sdl"},
        "_entities": [{"id": "1"}],
    }


def test_query_fields_are_matched_with_the_name_converter():
    class UpperCaseNameConverter(NameConverter):
        def get_graphql_name(self, obj: HasGraphQLName) -> str:
            return super().get_graphql_name(obj).upper()

    @strawberry.type(name="_Service")
    class CustomService:
        sdl: str

    @strawberry.type
    class Query:
        @strawberry.field(name="_service")
        def custom_service(self) -> CustomService:
            return CustomService(sdl="custom sdl")

    schema = strawberry.federation.Schema(
        query=Query, config=StrawberryConfig(name_converter=UpperCaseNameConverter())
    )

    result = schema.execute_sync("{ _SERVICE { SDL } }")

    assert not result.errors
    assert result.data == {"_SERVICE": {"SDL": "custom sdl"}}


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


def test_keeps_description_and_directives_of_query_type():
    @strawberry.federation.schema_directive(
        locations=[Location.OBJECT], name="cacheControl", compose=True
    )
    class CacheControl:
        max_age: int

    @strawberry.federation.type(
        description="The root query",
        shareable=True,
        directives=[CacheControl(max_age=10)],
    )
    class Query:
        hello: str

    schema = strawberry.federation.Schema(query=Query)

    expected = '''
        directive @cacheControl(maxAge: Int!) on OBJECT

        schema @composeDirective(name: "@cacheControl") @link(url: "https://directives.strawberry.rocks/cacheControl/v0.1", import: ["@cacheControl"]) @link(url: "https://specs.apollo.dev/federation/v2.11", import: ["@composeDirective", "@shareable"]) {
          query: Query
        }

        """The root query"""
        type Query @cacheControl(maxAge: 10) @shareable {
          _service: _Service!
          hello: String!
        }

        scalar _Any

        type _Service {
          sdl: String!
        }
    '''

    assert str(schema) == textwrap.dedent(expected).strip()


def test_federation_schema_warning():
    @strawberry.federation.type(keys=["upc"])
    class ProductFed:
        upc: str
        name: str | None
        price: int | None
        weight: int | None

    with pytest.warns(UserWarning) as record:  # noqa: PT030
        schema = strawberry.Schema(
            query=ProductFed,
        )

    assert (
        "Federation directive found in schema. "
        "Use `strawberry.federation.Schema` instead of `strawberry.Schema`."
        in [str(r.message) for r in record]
    )
    assert schema._schema.get_directive("key") is not None
    assert schema._schema.get_type("_FieldSet") is not None


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

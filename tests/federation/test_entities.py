import typing

from graphql import located_error

import strawberry
from strawberry.types import Info


def test_fetch_entities():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        def resolve_reference(cls, upc) -> "Product":
            return Product(upc=upc)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "upc": "B00005N5PF"}]
        },
    )

    assert not result.errors

    assert result.data == {"_entities": [{"upc": "B00005N5PF"}]}


def test_info_param_in_resolve_reference():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        debug_field_name: str

        @classmethod
        def resolve_reference(cls, info: strawberry.Info, upc: str) -> "Product":
            return Product(upc=upc, debug_field_name=info.field_name)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                    debugFieldName
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "upc": "B00005N5PF"}]
        },
    )

    assert not result.errors

    assert result.data == {
        "_entities": [
            {
                "upc": "B00005N5PF",
                # _entities is the field that's called by federation
                "debugFieldName": "_entities",
            }
        ]
    }


def test_does_not_need_custom_resolve_reference_for_basic_things():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "upc": "B00005N5PF"}]
        },
    )

    assert not result.errors

    assert result.data == {"_entities": [{"upc": "B00005N5PF"}]}


def test_does_not_need_custom_resolve_reference_nested():
    @strawberry.federation.type(keys=["id"])
    class Something:
        id: str

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        something: Something

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                    something {
                        id
                    }
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {"__typename": "Product", "upc": "B00005N5PF", "something": {"id": "1"}}
            ]
        },
    )

    assert not result.errors

    assert result.data == {
        "_entities": [{"upc": "B00005N5PF", "something": {"id": "1"}}]
    }


def test_fails_properly_when_wrong_key_is_passed():
    @strawberry.type
    class Something:
        id: str

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        something: Something

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                    something {
                        id
                    }
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "not_upc": "B00005N5PF"}]
        },
    )

    assert result.errors

    assert result.errors[0].message == "Unable to resolve reference for Product"


def test_fails_properly_when_wrong_data_is_passed():
    @strawberry.federation.type(keys=["id"])
    class Something:
        id: str

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        something: Something

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                    something {
                        id
                    }
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "upc": "B00005N5PF",
                    "not_something": {"id": "1"},
                }
            ]
        },
    )

    assert result.errors

    assert result.errors[0].message == "Unable to resolve reference for Product"


def test_propagates_original_error_message_with_auto_graphql_error_metadata():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

        @classmethod
        def resolve_reference(cls, id: strawberry.ID) -> "Product":
            raise Exception("Foo bar")

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def mock(self) -> typing.Optional[Product]:
            return None

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    id
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "id": "B00005N5PF",
                }
            ]
        },
    )

    assert len(result.errors) == 1
    error = result.errors[0].formatted
    assert error["message"] == "Foo bar"
    assert error["path"] == ["_entities", 0]
    assert error["locations"] == [{"column": 13, "line": 3}]
    assert "extensions" not in error


def test_propagates_custom_type_error_message_with_auto_graphql_error_metadata():
    class MyTypeError(TypeError):
        pass

    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

        @classmethod
        def resolve_reference(cls, id: strawberry.ID) -> "Product":
            raise MyTypeError("Foo bar")

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def mock(self) -> typing.Optional[Product]:
            return None

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    id
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "id": "B00005N5PF",
                }
            ]
        },
    )

    assert len(result.errors) == 1
    error = result.errors[0].formatted
    assert error["message"] == "Foo bar"
    assert error["path"] == ["_entities", 0]
    assert error["locations"] == [{"column": 13, "line": 3}]
    assert "extensions" not in error


def test_propagates_original_error_message_and_graphql_error_metadata():
    @strawberry.federation.type(keys=["id"])
    class Product:
        id: strawberry.ID

        @classmethod
        def resolve_reference(cls, info: Info, id: strawberry.ID) -> "Product":
            exception = Exception("Foo bar")
            exception.extensions = {"baz": "qux"}
            raise located_error(
                exception,
                nodes=info._raw_info.field_nodes[0],
                path=["_entities_override", 0],
            )

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def mock(self) -> typing.Optional[Product]:
            return None

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    id
                }
            }
        }
    """

    result = schema.execute_sync(
        query,
        variable_values={
            "representations": [
                {
                    "__typename": "Product",
                    "id": "B00005N5PF",
                }
            ]
        },
    )

    assert len(result.errors) == 1
    error = result.errors[0].formatted
    assert error["message"] == "Foo bar"
    assert error["path"] == ["_entities_override", 0]
    assert error["locations"] == [{"column": 13, "line": 3}]
    assert error["extensions"] == {"baz": "qux"}


async def test_can_use_async_resolve_reference():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        async def resolve_reference(cls, upc: str) -> "Product":
            return Product(upc=upc)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                }
            }
        }
    """

    result = await schema.execute(
        query,
        variable_values={
            "representations": [{"__typename": "Product", "upc": "B00005N5PF"}]
        },
    )

    assert not result.errors

    assert result.data == {"_entities": [{"upc": "B00005N5PF"}]}


async def test_can_use_async_resolve_reference_multiple_representations():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        async def resolve_reference(cls, upc: str) -> "Product":
            return Product(upc=upc)

    @strawberry.federation.type(extend=True)
    class Query:
        @strawberry.field
        def top_products(self, first: int) -> typing.List[Product]:  # pragma: no cover
            return []

    schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)

    query = """
        query ($representations: [_Any!]!) {
            _entities(representations: $representations) {
                ... on Product {
                    upc
                }
            }
        }
    """

    result = await schema.execute(
        query,
        variable_values={
            "representations": [
                {"__typename": "Product", "upc": "B00005N5PF"},
                {"__typename": "Product", "upc": "B00005N5PG"},
            ]
        },
    )

    assert not result.errors

    assert result.data == {"_entities": [{"upc": "B00005N5PF"}, {"upc": "B00005N5PG"}]}

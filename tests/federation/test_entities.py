import typing

import strawberry


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
        def top_products(self, first: int) -> typing.List[Product]:
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
        def top_products(self, first: int) -> typing.List[Product]:
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
        def top_products(self, first: int) -> typing.List[Product]:
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
        def top_products(self, first: int) -> typing.List[Product]:
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
        def top_products(self, first: int) -> typing.List[Product]:
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

    assert result.errors[0].message.startswith("Unable to resolve reference for")


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
        def top_products(self, first: int) -> typing.List[Product]:
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
        def top_products(self, first: int) -> typing.List[Product]:
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

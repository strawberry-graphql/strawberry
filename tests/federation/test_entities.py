import typing

import strawberry


def test_fetch_entities():
    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        def resolve_reference(cls, upc):
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
        info: str

        @classmethod
        def resolve_reference(cls, info, upc):
            return Product(upc=upc, info=info)

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
                    info
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

    assert (
        "GraphQLResolveInfo(field_name='_entities', field_nodes=[FieldNode"
        in result.data["_entities"][0]["info"]
    )


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
        async def resolve_reference(cls, upc: str):
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
        async def resolve_reference(cls, upc: str):
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


async def test_can_use_sync_resolve_references_multiple_representations():
    used_resolve_references = False

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        def resolve_reference(cls, upc: str):
            return Product(upc=upc)

        @classmethod
        def resolve_references(cls, upc: typing.List[str]):
            nonlocal used_resolve_references
            used_resolve_references = True
            return [Product(upc=upc_item) for upc_item in upc]

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
    assert used_resolve_references
    assert result.data == {"_entities": [{"upc": "B00005N5PF"}, {"upc": "B00005N5PG"}]}


async def test_can_use_async_resolve_references_multiple_representations():
    used_resolve_references = False

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        async def resolve_reference(cls, upc: str):
            return Product(upc=upc)

        @classmethod
        async def resolve_references(cls, upc: typing.List[str]):
            nonlocal used_resolve_references
            used_resolve_references = True
            return [Product(upc=upc_item) for upc_item in upc]

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
    assert used_resolve_references
    assert result.data == {"_entities": [{"upc": "B00005N5PF"}, {"upc": "B00005N5PG"}]}


async def test_got_confused_resolve_references():
    used_resolve_references = False

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str

        @classmethod
        async def resolve_reference(cls, upc: str):
            return Product(upc=upc)

        @classmethod
        async def resolve_references(cls, upcs: typing.List[str]):
            nonlocal used_resolve_references
            used_resolve_references = True
            return [Product(upc=upc_item) for upc_item in upcs]

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

    assert result.errors
    assert result.errors[0].message.startswith(
        "Got confused while trying use resolve_references for"
    )

async def test_info_param_in_resolve_references():
    used_resolve_references = False

    @strawberry.federation.type(keys=["upc"])
    class Product:
        upc: str
        info: str

        @classmethod
        def resolve_reference(cls, info, upc):
            return Product(upc=upc, info=info)

        @classmethod
        def resolve_references(cls, info, upc: typing.List[str]):
            nonlocal used_resolve_references
            used_resolve_references = True
            return [Product(upc=upc_item, info=info) for upc_item in upc]

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
                    info
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
    assert used_resolve_references

    assert (
        "GraphQLResolveInfo(field_name='_entities', field_nodes=[FieldNode"
        in result.data["_entities"][0]["info"]
    )
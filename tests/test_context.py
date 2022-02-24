import asyncio
import random
from typing import List

import pytest

import strawberry
from strawberry.context import context
from strawberry.types.info import Info


def test_context_sync():
    def some_resolver(root, info: Info) -> str:
        assert context.root is root
        assert isinstance(context.root, Foo)
        assert context.info is info
        return f"{context.info.field_name}: {context.root.name}"

    @strawberry.type
    class Foo:
        name: str
        some_field = strawberry.field(resolver=some_resolver)

        @strawberry.field
        def other_field(self, root, info: Info) -> str:
            assert context.root is root
            assert isinstance(context.root, Foo)
            assert context.info is info
            return f"{context.info.field_name}: {context.root.name}"

        @strawberry.field
        def no_params_field(self) -> str:
            return f"{context.info.field_name}: {context.root.name}"

    @strawberry.type
    class Query:
        @strawberry.field
        def foo_list(self, root, info: Info) -> List[Foo]:
            assert root is None
            assert context.root is None
            assert context.info is info

            return [Foo(name=f"Foo {i}") for i in range(2)]

    schema = strawberry.Schema(query=Query)
    query = """
    query MyQuery {
        fooList {
            name
            someField
            otherField
            noParamsField
        }
    }
    """
    result = schema.execute_sync(query, variable_values={})

    assert not result.errors
    assert result.data == {
        "fooList": [
            {
                "name": "Foo 0",
                "someField": "someField: Foo 0",
                "otherField": "otherField: Foo 0",
                "noParamsField": "noParamsField: Foo 0",
            },
            {
                "name": "Foo 1",
                "someField": "someField: Foo 1",
                "otherField": "otherField: Foo 1",
                "noParamsField": "noParamsField: Foo 1",
            },
        ]
    }


@pytest.mark.asyncio
async def test_context_async():
    async def some_resolver(root, info: Info) -> str:
        # Some mess to make sure resolvers are inside their ctx at the same time
        await asyncio.sleep(random.random())
        assert context.root is root
        assert isinstance(context.root, Foo)
        assert context.info is info
        return f"{context.info.field_name}: {context.root.name}"

    @strawberry.type
    class Foo:
        name: str
        some_field = strawberry.field(resolver=some_resolver)

        @strawberry.field
        async def other_field(self, root, info: Info) -> str:
            # Some mess to make sure resolvers are inside their ctx at the same time
            await asyncio.sleep(random.random())
            assert context.root is root
            assert isinstance(context.root, Foo)
            assert context.info is info
            return f"{context.info.field_name}: {context.root.name}"

        @strawberry.field
        async def no_params_field(self) -> str:
            # Some mess to make sure resolvers are inside their ctx at the same time
            await asyncio.sleep(random.random())
            return f"{context.info.field_name}: {context.root.name}"

    @strawberry.type
    class Query:
        @strawberry.field
        async def foo_list(self, root, info: Info) -> List[Foo]:
            # Some mess to make sure resolvers are inside their ctx at the same time
            await asyncio.sleep(random.random())
            assert root is None
            assert context.root is None
            assert context.info is info

            return [Foo(name=f"Foo {i}") for i in range(2)]

    schema = strawberry.Schema(query=Query)
    query = """
    query MyQuery {
        fooList {
            name
            someField
            otherField
            noParamsField
        }
        otherFooList: fooList {
            name
            someField
            otherField
            noParamsField
        }
    }
    """
    result = await schema.execute(query, variable_values={})

    assert not result.errors
    assert result.data == {
        "fooList": [
            {
                "name": "Foo 0",
                "someField": "someField: Foo 0",
                "otherField": "otherField: Foo 0",
                "noParamsField": "noParamsField: Foo 0",
            },
            {
                "name": "Foo 1",
                "someField": "someField: Foo 1",
                "otherField": "otherField: Foo 1",
                "noParamsField": "noParamsField: Foo 1",
            },
        ],
        "otherFooList": [
            {
                "name": "Foo 0",
                "someField": "someField: Foo 0",
                "otherField": "otherField: Foo 0",
                "noParamsField": "noParamsField: Foo 0",
            },
            {
                "name": "Foo 1",
                "someField": "someField: Foo 1",
                "otherField": "otherField: Foo 1",
                "noParamsField": "noParamsField: Foo 1",
            },
        ],
    }

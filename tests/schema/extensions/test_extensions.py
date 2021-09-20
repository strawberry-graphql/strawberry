import pytest

import strawberry
from strawberry.extensions import Extension


def test_base_extension():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[Extension])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.extensions == {}


def test_extension():
    class MyExtension(Extension):
        def get_results(self):
            return {"example": "example"}

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors

    assert result.extensions == {
        "example": "example",
    }


@pytest.mark.asyncio
async def test_extension_async():
    class MyExtension(Extension):
        def get_results(self):
            return {"example": "example"}

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        async def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query {
            person {
                name
            }
        }
    """

    result = await schema.execute(query)

    assert not result.errors

    assert result.extensions == {
        "example": "example",
    }


def test_extension_access_to_parsed_document():
    query_name = ""

    class MyExtension(Extension):
        def on_parsing_end(self):
            nonlocal query_name
            query_definition = self.execution_context.graphql_document.definitions[0]
            query_name = query_definition.name.value

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query TestQuery {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert query_name == "TestQuery"


def test_extension_access_to_errors():
    execution_errors = []

    class MyExtension(Extension):
        def on_request_end(self):
            nonlocal execution_errors
            execution_errors = self.execution_context.errors

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return None  # type: ignore

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query TestQuery {
            person {
                name
            }
        }
    """

    result = schema.execute_sync(query)

    assert len(result.errors) == 1
    assert execution_errors == result.errors


def test_extension_access_to_root_value():
    root_value = None

    class MyExtension(Extension):
        def on_request_end(self):
            nonlocal root_value
            root_value = self.execution_context.root_value

    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self) -> str:
            return "👋"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = "{ hi }"

    result = schema.execute_sync(query, root_value="ROOT")

    assert not result.errors
    assert root_value == "ROOT"


@pytest.mark.asyncio
async def test_async_extension_hooks():
    called_hooks = set()

    class MyExtension(Extension):
        async def on_request_start(self):
            called_hooks.add(1)

        async def on_request_end(self):
            called_hooks.add(2)

        async def on_validation_start(self):
            called_hooks.add(3)

        async def on_validation_end(self):
            called_hooks.add(4)

        async def on_parsing_start(self):
            called_hooks.add(5)

        async def on_parsing_end(self):
            called_hooks.add(6)

        async def get_results(self):
            called_hooks.add(7)
            return {"example": "example"}

        async def resolve(self, _next, root, info, *args, **kwargs):
            called_hooks.add(8)
            return _next(root, info, *args, **kwargs)

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query TestQuery { person { name } }"

    result = await schema.execute(query)
    assert result.errors is None

    assert called_hooks == {1, 2, 3, 4, 5, 6, 7, 8}


@pytest.mark.asyncio
async def test_mixed_sync_and_async_extension_hooks():
    called_hooks = set()

    class MyExtension(Extension):
        def on_request_start(self):
            called_hooks.add(1)

        async def on_request_end(self):
            called_hooks.add(2)

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query TestQuery { person { name } }"

    result = await schema.execute(query)
    assert result.errors is None

    assert called_hooks == {1, 2}


def test_warning_about_async_get_results_hooks_in_sync_context():
    class MyExtension(Extension):
        async def get_results(self):
            pass

    @strawberry.type
    class Query:
        @strawberry.field
        def string(self) -> str:
            return str()

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { string }"

    with pytest.raises(RuntimeError) as exc_info:
        schema.execute_sync(query)
        msg = "Cannot use async extension hook during sync execution"
        assert str(exc_info.value) == msg

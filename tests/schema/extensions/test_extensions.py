import pytest

import strawberry
from strawberry.extensions import Extension
from strawberry.extensions.constants import (
    GET_RESULTS,
    ON_PARSING_END,
    ON_PARSING_START,
    ON_REQUEST_END,
    ON_REQUEST_START,
    ON_VALIDATION_END,
    ON_VALIDATION_START,
    RESOLVE,
    SYNC_CONTEXT_WARNING,
)


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
            called_hooks.add(ON_REQUEST_START)

        async def on_request_end(self):
            called_hooks.add(ON_REQUEST_END)

        async def on_validation_start(self):
            called_hooks.add(ON_VALIDATION_START)

        async def on_validation_end(self):
            called_hooks.add(ON_VALIDATION_END)

        async def on_parsing_start(self):
            called_hooks.add(ON_PARSING_START)

        async def on_parsing_end(self):
            called_hooks.add(ON_PARSING_END)

        async def get_results(self):
            called_hooks.add(GET_RESULTS)
            return {"example": "example"}

        async def resolve(self, _next, root, info, *args, **kwargs):
            called_hooks.add(RESOLVE)
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

    assert called_hooks == {
        ON_REQUEST_END,
        ON_REQUEST_START,
        ON_VALIDATION_END,
        ON_VALIDATION_START,
        ON_PARSING_END,
        ON_PARSING_START,
        GET_RESULTS,
        RESOLVE,
    }


@pytest.mark.asyncio
async def test_mixed_sync_and_async_extension_hooks():
    called_hooks = set()

    class MyExtension(Extension):
        def on_request_start(self):
            called_hooks.add(ON_REQUEST_START)

        async def on_request_end(self):
            called_hooks.add(ON_REQUEST_END)

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

    assert called_hooks == {ON_REQUEST_END, ON_REQUEST_START}


def test_warning_about_async_context_hooks_in_sync_context():
    class MyExtension(Extension):
        async def on_request_start(self):
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
        assert str(exc_info.value) == SYNC_CONTEXT_WARNING


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
        assert str(exc_info.value) == SYNC_CONTEXT_WARNING

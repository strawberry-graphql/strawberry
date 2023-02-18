import json
from typing import Dict, List, Optional
from unittest.mock import patch

import pytest
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError
from graphql import execute as original_execute

import strawberry
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions import SchemaExtension


def test_base_extension():
    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[SchemaExtension])

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
    class MyExtension(SchemaExtension):
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
    class MyExtension(SchemaExtension):
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

    class MyExtension(SchemaExtension):
        def on_parsing_end(self):
            nonlocal query_name
            assert self.execution_context.graphql_document
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
    execution_errors: Optional[List[GraphQLError]] = []

    class MyExtension(SchemaExtension):
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

    assert result.errors
    assert len(result.errors) == 1
    assert execution_errors == result.errors


def test_extension_access_to_root_value():
    root_value = None

    class MyExtension(SchemaExtension):
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

    class MyExtension(SchemaExtension):
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

    class MyExtension(SchemaExtension):
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
    class MyExtension(SchemaExtension):
        async def get_results(self):
            pass

    @strawberry.type
    class Query:
        @strawberry.field
        def string(self) -> str:
            return ""

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { string }"

    with pytest.raises(RuntimeError) as exc_info:
        schema.execute_sync(query)
        msg = "Cannot use async extension hook during sync execution"
        assert str(exc_info.value) == msg


@pytest.mark.asyncio
async def test_dont_swallow_errors_in_parsing_hooks():
    class MyExtension(SchemaExtension):
        def on_parsing_start(self):
            raise Exception("This shouldn't be swallowed")

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { string }"

    with pytest.raises(Exception, match="This shouldn't be swallowed"):
        schema.execute_sync(query)

    with pytest.raises(Exception, match="This shouldn't be swallowed"):
        await schema.execute(query)


def test_on_parsing_end_called_when_errors():
    execution_errors = None

    class MyExtension(SchemaExtension):
        def on_parsing_end(self):
            nonlocal execution_errors
            execution_context = self.execution_context
            execution_errors = execution_context.errors

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { string"  # Invalid query

    result = schema.execute_sync(query)
    assert result.errors

    assert result.errors == execution_errors


def test_extension_override_execution():
    class MyExtension(SchemaExtension):
        def on_executing_start(self):
            # Always return a static response
            self.execution_context.result = GraphQLExecutionResult(
                data={
                    "surprise": "data",
                },
                errors=[],
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query TestQuery {
            ping
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {
        "surprise": "data",
    }


@pytest.mark.asyncio
async def test_extension_override_execution_async():
    class MyExtension(SchemaExtension):
        def on_executing_start(self):
            # Always return a static response
            self.execution_context.result = GraphQLExecutionResult(
                data={
                    "surprise": "data",
                },
                errors=[],
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    query = """
        query TestQuery {
            ping
        }
    """

    result = await schema.execute(query)

    assert not result.errors
    assert result.data == {
        "surprise": "data",
    }


@patch("strawberry.schema.execute.original_execute", wraps=original_execute)
def test_execution_cache_example(mock_original_execute):
    # Test that the example of how to use the on_executing_start hook in the
    # docs actually works

    response_cache: Dict[str, Optional[GraphQLExecutionResult]] = {}

    class ExecutionCache(SchemaExtension):
        def on_executing_start(self):
            # Check if we've come across this query before
            execution_context = self.execution_context
            self.cache_key = (
                f"{execution_context.query}:{json.dumps(execution_context.variables)}"
            )
            if self.cache_key in response_cache:
                self.execution_context.result = response_cache[self.cache_key]

        def on_executing_end(self):
            execution_context = self.execution_context
            if self.cache_key not in response_cache:
                response_cache[self.cache_key] = execution_context.result

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self, return_value: Optional[str] = None) -> str:
            if return_value is not None:
                return return_value
            return "pong"

    schema = strawberry.Schema(
        Query,
        extensions=[
            ExecutionCache,
        ],
    )

    query = """
        query TestQuery($returnValue: String) {
            ping(returnValue: $returnValue)
        }
    """
    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data == {
        "ping": "pong",
    }

    assert mock_original_execute.call_count == 1

    # This should be cached
    result = schema.execute_sync(query)
    assert not result.errors
    assert result.data == {
        "ping": "pong",
    }

    assert mock_original_execute.call_count == 1

    # Calling with different variables should not be cached
    result = schema.execute_sync(
        query,
        variable_values={
            "returnValue": "plong",
        },
    )
    assert not result.errors
    assert result.data == {
        "ping": "plong",
    }

    assert mock_original_execute.call_count == 2


@patch("strawberry.schema.execute.original_execute", wraps=original_execute)
def test_execution_reject_example(mock_original_execute):
    # Test that the example of how to use the on_executing_start hook in the
    # docs actually works

    class RejectSomeQueries(SchemaExtension):
        def on_executing_start(self):
            # Reject all operations called "RejectMe"
            execution_context = self.execution_context
            if execution_context.operation_name == "RejectMe":
                self.execution_context.result = GraphQLExecutionResult(
                    data=None,
                    errors=[GraphQLError("Well you asked for it")],
                )

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(
        Query,
        extensions=[
            RejectSomeQueries,
        ],
    )

    query = """
        query TestQuery {
            ping
        }
    """
    result = schema.execute_sync(query, operation_name="TestQuery")
    assert not result.errors
    assert result.data == {
        "ping": "pong",
    }

    assert mock_original_execute.call_count == 1

    query = """
        query RejectMe {
            ping
        }
    """
    result = schema.execute_sync(query, operation_name="RejectMe")
    assert result.errors == [GraphQLError("Well you asked for it")]

    assert mock_original_execute.call_count == 1


def test_extend_error_format_example():
    # Test that the example of how to extend error format

    class ExtendErrorFormat(SchemaExtension):
        def on_request_end(self):
            result = self.execution_context.result
            if getattr(result, "errors", None):
                result.errors = [
                    StrawberryGraphQLError(
                        extensions={"additional_key": "additional_value"},
                        nodes=error.nodes,
                        source=error.source,
                        positions=error.positions,
                        path=error.path,
                        original_error=error.original_error,
                        message=error.message,
                    )
                    for error in result.errors
                ]

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            raise Exception("This error occurred while querying the ping field")

    schema = strawberry.Schema(query=Query, extensions=[ExtendErrorFormat])
    query = """
        query TestQuery {
            ping
        }
    """

    result = schema.execute_sync(query)
    assert result.errors[0].extensions == {"additional_key": "additional_value"}
    assert (
        result.errors[0].message == "This error occurred while querying the ping field"
    )
    assert result.data is None


def test_extension_can_set_query():
    class MyExtension(SchemaExtension):
        def on_request_start(self):
            self.execution_context.query = "{ hi }"

    @strawberry.type
    class Query:
        @strawberry.field
        def hi(self) -> str:
            return "👋"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    # Query not set on input
    query = ""

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == {"hi": "👋"}


@pytest.mark.asyncio
async def test_extension_can_set_query_async():
    class MyExtension(SchemaExtension):
        def on_request_start(self):
            self.execution_context.query = "{ hi }"

    @strawberry.type
    class Query:
        @strawberry.field
        async def hi(self) -> str:
            return "👋"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])

    # Query not set on input
    query = ""

    result = await schema.execute(query)

    assert not result.errors
    assert result.data == {"hi": "👋"}

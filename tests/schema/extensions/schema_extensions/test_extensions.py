import contextlib
import json
import warnings
from typing import Any, Optional
from unittest.mock import patch

import pytest
from graphql import ExecutionResult as GraphQLExecutionResult
from graphql import GraphQLError
from graphql import execute as original_execute

import strawberry
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions import SchemaExtension

from .conftest import ExampleExtension, ExecType, SchemaHelper, hook_wrap


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


def test_called_only_if_overriden(monkeypatch: pytest.MonkeyPatch):
    called = False

    def dont_call_me(self_):
        nonlocal called
        called = True

    class ExtensionNoHooks(SchemaExtension): ...

    for hook in (
        ExtensionNoHooks.on_parse,
        ExtensionNoHooks.on_operation,
        ExtensionNoHooks.on_execute,
        ExtensionNoHooks.on_validate,
    ):
        monkeypatch.setattr(SchemaExtension, hook.__name__, dont_call_me)

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(query=Query, extensions=[ExtensionNoHooks])

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
    assert not called


def test_extension_access_to_parsed_document():
    query_name = ""

    class MyExtension(SchemaExtension):
        def on_parse(self):
            nonlocal query_name
            yield
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

    class MyExtension(SchemaExtension):
        def on_operation(self):
            nonlocal execution_errors
            yield
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

    class MyExtension(SchemaExtension):
        def on_operation(self):
            nonlocal root_value
            yield
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


def test_can_initialize_extension(default_query_types_and_query):
    class CustomizableExtension(SchemaExtension):
        def __init__(self, arg: int):
            self.arg = arg

        def on_operation(self):
            yield
            self.execution_context.result.data = {"override": self.arg}

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        extensions=[
            CustomizableExtension(20),
        ],
    )
    res = schema.execute_sync(query=default_query_types_and_query.query)
    assert not res.errors
    assert res.data == {"override": 20}


@pytest.fixture
def sync_extension() -> type[ExampleExtension]:
    class MyExtension(ExampleExtension):
        def on_operation(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_operation.__name__):
                yield

        def on_validate(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_validate.__name__):
                yield

        def on_parse(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_parse.__name__):
                yield

        def on_execute(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_execute.__name__):
                yield

        def get_results(self):
            self.called_hooks.append("get_results")
            return {"example": "example"}

        def resolve(self, _next, root, info, *args: str, **kwargs: Any):
            self.called_hooks.append("resolve")
            return _next(root, info, *args, **kwargs)

    return MyExtension


@pytest.mark.asyncio
async def test_async_extension_hooks(
    default_query_types_and_query: SchemaHelper, async_extension: type[ExampleExtension]
):
    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type, extensions=[async_extension]
    )

    result = await schema.execute(default_query_types_and_query.query)
    assert result.errors is None

    async_extension.assert_expected()


@pytest.mark.asyncio
async def test_mixed_sync_and_async_extension_hooks(
    default_query_types_and_query, sync_extension
):
    class MyExtension(sync_extension):
        async def on_operation(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_operation.__name__):
                yield

        async def on_parse(self):
            with hook_wrap(self.called_hooks, SchemaExtension.on_parse.__name__):
                yield

    @strawberry.type
    class Person:
        name: str = "Jess"

    @strawberry.type
    class Query:
        @strawberry.field
        def person(self) -> Person:
            return Person()

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type, extensions=[MyExtension]
    )
    result = await schema.execute(default_query_types_and_query.query)
    assert result.errors is None
    MyExtension.assert_expected()


async def test_execution_order(default_query_types_and_query):
    called_hooks = []

    @contextlib.contextmanager
    def register_hook(hook_name: str, klass: type):
        called_hooks.append(f"{klass.__name__}, {hook_name} Entered")
        yield
        called_hooks.append(f"{klass.__name__}, {hook_name} Exited")

    class ExtensionA(ExampleExtension):
        async def on_operation(self):
            with register_hook(SchemaExtension.on_operation.__name__, ExtensionA):
                yield

        async def on_parse(self):
            with register_hook(SchemaExtension.on_parse.__name__, ExtensionA):
                yield

        def on_validate(self):
            with register_hook(SchemaExtension.on_validate.__name__, ExtensionA):
                yield

        def on_execute(self):
            with register_hook(SchemaExtension.on_execute.__name__, ExtensionA):
                yield

    class ExtensionB(ExampleExtension):
        async def on_operation(self):
            with register_hook(SchemaExtension.on_operation.__name__, ExtensionB):
                yield

        def on_parse(self):
            with register_hook(SchemaExtension.on_parse.__name__, ExtensionB):
                yield

        def on_validate(self):
            with register_hook(SchemaExtension.on_validate.__name__, ExtensionB):
                yield

        async def on_execute(self):
            with register_hook(SchemaExtension.on_execute.__name__, ExtensionB):
                yield

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        extensions=[ExtensionA, ExtensionB],
    )
    result = await schema.execute(default_query_types_and_query.query)
    assert result.errors is None
    assert called_hooks == [
        "ExtensionA, on_operation Entered",
        "ExtensionB, on_operation Entered",
        "ExtensionA, on_parse Entered",
        "ExtensionB, on_parse Entered",
        "ExtensionB, on_parse Exited",
        "ExtensionA, on_parse Exited",
        "ExtensionA, on_validate Entered",
        "ExtensionB, on_validate Entered",
        "ExtensionB, on_validate Exited",
        "ExtensionA, on_validate Exited",
        "ExtensionA, on_execute Entered",
        "ExtensionB, on_execute Entered",
        "ExtensionB, on_execute Exited",
        "ExtensionA, on_execute Exited",
        "ExtensionB, on_operation Exited",
        "ExtensionA, on_operation Exited",
    ]


async def test_sync_extension_hooks(default_query_types_and_query, sync_extension):
    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type,
        extensions=[
            sync_extension,
        ],
    )

    result = schema.execute_sync(default_query_types_and_query.query)
    assert result.errors is None

    sync_extension.assert_expected()


async def test_extension_no_yield(default_query_types_and_query):
    class SyncExt(ExampleExtension):
        expected = [
            f"{SchemaExtension.on_operation.__name__} Entered",
            f"{SchemaExtension.on_parse.__name__} Entered",
        ]

        def on_operation(self):
            self.called_hooks.append(self.__class__.expected[0])

        async def on_parse(self):
            self.called_hooks.append(self.__class__.expected[1])

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type, extensions=[SyncExt]
    )

    result = await schema.execute(default_query_types_and_query.query)
    assert result.errors is None

    SyncExt.assert_expected()


def test_raise_if_defined_both_legacy_and_new_style(default_query_types_and_query):
    class WrongUsageExtension(SchemaExtension):
        def on_execute(self):
            yield

        def on_executing_start(self): ...

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type, extensions=[WrongUsageExtension]
    )
    result = schema.execute_sync(default_query_types_and_query.query)
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, ValueError)


async def test_legacy_extension_supported():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message=r"'.*' is deprecated and slated for removal in Python 3\.\d+",
        )

        class CompatExtension(ExampleExtension):
            async def on_request_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_operation.__name__} Entered"
                )

            async def on_request_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_operation.__name__} Exited"
                )

            async def on_validation_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_validate.__name__} Entered"
                )

            async def on_validation_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_validate.__name__} Exited"
                )

            async def on_parsing_start(self):
                self.called_hooks.append(f"{SchemaExtension.on_parse.__name__} Entered")

            async def on_parsing_end(self):
                self.called_hooks.append(f"{SchemaExtension.on_parse.__name__} Exited")

            def on_executing_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_execute.__name__} Entered"
                )

            def on_executing_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_execute.__name__} Exited"
                )

        @strawberry.type
        class Person:
            name: str = "Jess"

        @strawberry.type
        class Query:
            @strawberry.field
            def person(self) -> Person:
                return Person()

        schema = strawberry.Schema(query=Query, extensions=[CompatExtension])
        query = "query TestQuery { person { name } }"

        result = await schema.execute(query)
        assert result.errors is None

        assert CompatExtension.called_hooks == list(
            filter(lambda x: x.startswith("on_"), ExampleExtension.expected)
        )
        assert "Event driven styled extensions for" in w[0].message.args[0]


async def test_legacy_only_start():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message=r"'.*' is deprecated and slated for removal in Python 3\.\d+",
        )

        class CompatExtension(ExampleExtension):
            expected = list(
                filter(lambda x: x.endswith(" Entered"), ExampleExtension.expected)
            )

            async def on_request_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_operation.__name__} Entered"
                )

            async def on_validation_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_validate.__name__} Entered"
                )

            async def on_parsing_start(self):
                self.called_hooks.append(f"{SchemaExtension.on_parse.__name__} Entered")

            def on_executing_start(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_execute.__name__} Entered"
                )

        @strawberry.type
        class Person:
            name: str = "Jess"

        @strawberry.type
        class Query:
            @strawberry.field
            def person(self) -> Person:
                return Person()

        schema = strawberry.Schema(query=Query, extensions=[CompatExtension])
        query = "query TestQuery { person { name } }"

        result = await schema.execute(query)
        assert result.errors is None

        CompatExtension.assert_expected()
        assert "Event driven styled extensions for" in w[0].message.args[0]


async def test_legacy_only_end():
    with warnings.catch_warnings(record=True) as w:
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            message=r"'.*' is deprecated and slated for removal in Python 3\.\d+",
        )

        class CompatExtension(ExampleExtension):
            expected = list(
                filter(lambda x: x.endswith(" Exited"), ExampleExtension.expected)
            )

            async def on_request_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_operation.__name__} Exited"
                )

            async def on_validation_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_validate.__name__} Exited"
                )

            async def on_parsing_end(self):
                self.called_hooks.append(f"{SchemaExtension.on_parse.__name__} Exited")

            def on_executing_end(self):
                self.called_hooks.append(
                    f"{SchemaExtension.on_execute.__name__} Exited"
                )

        @strawberry.type
        class Person:
            name: str = "Jess"

        @strawberry.type
        class Query:
            @strawberry.field
            def person(self) -> Person:
                return Person()

        schema = strawberry.Schema(query=Query, extensions=[CompatExtension])
        query = "query TestQuery { person { name } }"

        result = await schema.execute(query)
        assert result.errors is None

        CompatExtension.assert_expected()
        assert "Event driven styled extensions for" in w[0].message.args[0]


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

    with pytest.raises(
        RuntimeError, match="Cannot use async extension hook during sync execution"
    ):
        schema.execute_sync(query)


class ExceptionTestingExtension(SchemaExtension):
    def __init__(self, failing_hook: str):
        self.failing_hook = failing_hook
        self.called_hooks = set()

    def on_operation(self):
        if self.failing_hook == "on_operation_start":
            raise Exception(self.failing_hook)
        self.called_hooks.add(1)

        with contextlib.suppress(Exception):
            yield

        if self.failing_hook == "on_operation_end":
            raise Exception(self.failing_hook)
        self.called_hooks.add(8)

    def on_parse(self):
        if self.failing_hook == "on_parse_start":
            raise Exception(self.failing_hook)
        self.called_hooks.add(2)

        with contextlib.suppress(Exception):
            yield

        if self.failing_hook == "on_parse_end":
            raise Exception(self.failing_hook)
        self.called_hooks.add(3)

    def on_validate(self):
        if self.failing_hook == "on_validate_start":
            raise Exception(self.failing_hook)
        self.called_hooks.add(4)

        with contextlib.suppress(Exception):
            yield

        if self.failing_hook == "on_validate_end":
            raise Exception(self.failing_hook)
        self.called_hooks.add(5)

    def on_execute(self):
        if self.failing_hook == "on_execute_start":
            raise Exception(self.failing_hook)
        self.called_hooks.add(6)

        with contextlib.suppress(Exception):
            yield

        if self.failing_hook == "on_execute_end":
            raise Exception(self.failing_hook)
        self.called_hooks.add(7)


@pytest.mark.parametrize(
    "failing_hook",
    [
        "on_operation_start",
        "on_operation_end",
        "on_parse_start",
        "on_parse_end",
        "on_validate_start",
        "on_validate_end",
        "on_execute_start",
        "on_execute_end",
    ],
)
@pytest.mark.asyncio
async def test_exceptions_are_included_in_the_execution_result(failing_hook):
    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(
        query=Query,
        extensions=[ExceptionTestingExtension(failing_hook)],
    )
    document = "query { ping }"

    sync_result = schema.execute_sync(document)
    assert sync_result.errors is not None
    assert len(sync_result.errors) == 1
    assert sync_result.errors[0].message == failing_hook

    async_result = await schema.execute(document)
    assert async_result.errors is not None
    assert len(async_result.errors) == 1
    assert sync_result.errors[0].message == failing_hook


@pytest.mark.parametrize(
    ("failing_hook", "expected_hooks"),
    [
        ("on_operation_start", set()),
        ("on_parse_start", {1, 8}),
        ("on_parse_end", {1, 2, 8}),
        ("on_validate_start", {1, 2, 3, 8}),
        ("on_validate_end", {1, 2, 3, 4, 8}),
        ("on_execute_start", {1, 2, 3, 4, 5, 8}),
        ("on_execute_end", {1, 2, 3, 4, 5, 6, 8}),
        ("on_operation_end", {1, 2, 3, 4, 5, 6, 7}),
    ],
)
@pytest.mark.asyncio
async def test_exceptions_abort_evaluation(failing_hook, expected_hooks):
    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    extension = ExceptionTestingExtension(failing_hook)
    schema = strawberry.Schema(query=Query, extensions=[extension])
    document = "query { ping }"

    extension.called_hooks = set()
    schema.execute_sync(document)
    assert extension.called_hooks == expected_hooks

    extension.called_hooks = set()
    await schema.execute(document)
    assert extension.called_hooks == expected_hooks


async def test_generic_exceptions_get_wrapped_in_a_graphql_error(
    exec_type: ExecType,
) -> None:
    exception = Exception("This should be wrapped in a GraphQL error")

    class MyExtension(SchemaExtension):
        def on_parse(self):
            raise exception

    @strawberry.type
    class Query:
        ping: str = "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { ping }"
    if exec_type.is_async():
        res = await schema.execute(query)
    else:
        res = schema.execute_sync(query)

    res = await schema.execute(query)
    assert len(res.errors) == 1
    assert isinstance(res.errors[0], GraphQLError)
    assert res.errors[0].original_error == exception


async def test_graphql_errors_get_not_wrapped_in_a_graphql_error(
    exec_type: ExecType,
) -> None:
    exception = GraphQLError("This should not be wrapped in a GraphQL error")

    class MyExtension(SchemaExtension):
        def on_parse(self):
            raise exception

    @strawberry.type
    class Query:
        ping: str = "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { ping }"
    if exec_type.is_async():
        res = await schema.execute(query)
    else:
        res = schema.execute_sync(query)
    assert len(res.errors) == 1
    assert res.errors[0] == exception
    assert res.errors[0].original_error is None


@pytest.mark.asyncio
async def test_dont_swallow_errors_in_parsing_hooks():
    class MyExtension(SchemaExtension):
        def on_parse(self):
            raise Exception("This shouldn't be swallowed")

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> str:
            return "pong"

    schema = strawberry.Schema(query=Query, extensions=[MyExtension])
    query = "query { string }"

    sync_result = schema.execute_sync(query)
    assert len(sync_result.errors) == 1
    assert sync_result.errors[0].message == "This shouldn't be swallowed"

    async_result = await schema.execute(query)
    assert len(async_result.errors) == 1
    assert async_result.errors[0].message == "This shouldn't be swallowed"


def test_on_parsing_end_is_called_with_parsing_errors():
    execution_errors = False

    class MyExtension(SchemaExtension):
        def on_parse(self):
            nonlocal execution_errors
            yield
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


def test_extension_execution_order_sync():
    """Ensure mixed hooks (async & sync) are called correctly."""
    execution_order: list[type[SchemaExtension]] = []

    class ExtensionB(SchemaExtension):
        def on_execute(self):
            execution_order.append(type(self))
            yield
            execution_order.append(type(self))

    class ExtensionC(SchemaExtension):
        def on_execute(self):
            execution_order.append(type(self))
            yield
            execution_order.append(type(self))

    @strawberry.type
    class Query:
        food: str = "strawberry"

    extensions = [ExtensionB, ExtensionC]
    schema = strawberry.Schema(query=Query, extensions=extensions)

    query = """
        query TestQuery {
            food
        }
    """

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data == {"food": "strawberry"}
    assert execution_order == [ExtensionB, ExtensionC, ExtensionC, ExtensionB]


def test_async_extension_in_sync_context():
    class ExtensionA(SchemaExtension):
        async def on_execute(self):
            yield

    @strawberry.type
    class Query:
        food: str = "strawberry"

    schema = strawberry.Schema(query=Query, extensions=[ExtensionA])

    result = schema.execute_sync("query { food }")
    assert len(result.errors) == 1
    assert result.errors[0].message.endswith("failed to complete synchronously.")


def test_extension_override_execution():
    class MyExtension(SchemaExtension):
        def on_execute(self):
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
        def on_execute(self):
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


@patch("strawberry.schema.schema.execute", wraps=original_execute)
def test_execution_cache_example(mock_original_execute):
    # Test that the example of how to use the on_executing_start hook in the
    # docs actually works

    response_cache = {}

    class ExecutionCache(SchemaExtension):
        def on_execute(self):
            # Check if we've come across this query before
            execution_context = self.execution_context
            self.cache_key = (
                f"{execution_context.query}:{json.dumps(execution_context.variables)}"
            )
            if self.cache_key in response_cache:
                self.execution_context.result = response_cache[self.cache_key]
            yield
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


@patch("strawberry.schema.schema.execute", wraps=original_execute)
def test_execution_reject_example(mock_original_execute):
    # Test that the example of how to use the on_executing_start hook in the
    # docs actually works

    class RejectSomeQueries(SchemaExtension):
        def on_execute(self):
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
        def on_operation(self):
            yield
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
        def on_operation(self):
            self.execution_context.query = "{ hi }"
            yield

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
        def on_operation(self):
            self.execution_context.query = "{ hi }"
            yield

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


def test_raise_if_hook_is_not_callable(default_query_types_and_query: SchemaHelper):
    class MyExtension(SchemaExtension):
        on_operation = "ABC"  # type: ignore

    schema = strawberry.Schema(
        query=default_query_types_and_query.query_type, extensions=[MyExtension]
    )
    result = schema.execute_sync(default_query_types_and_query.query)
    assert len(result.errors) == 1
    assert isinstance(result.errors[0].original_error, ValueError)
    assert result.errors[0].message.startswith("Hook on_operation on <")
    assert result.errors[0].message.endswith("> must be callable, received 'ABC'")

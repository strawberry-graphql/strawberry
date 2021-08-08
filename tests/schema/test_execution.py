import textwrap
from typing import Optional

import pytest

from graphql import GraphQLError, ValidationRule

import strawberry
from strawberry.schema import default_validation_rules


@pytest.mark.parametrize("validate_queries", (True, False))
def test_enabling_query_validation_sync(validate_queries, mocker):
    extension_mock = mocker.Mock()
    extension_mock.get_results.return_value = {}

    extension_class_mock = mocker.Mock(return_value=extension_mock)

    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(
        query=Query,
        extensions=[extension_class_mock],
    )

    query = """
        query {
            example
        }
    """

    result = schema.execute_sync(
        query,
        root_value=Query(),
        validate_queries=validate_queries,
    )

    assert not result.errors

    assert extension_mock.on_validation_start.called is validate_queries
    assert extension_mock.on_validation_end.called is validate_queries


@pytest.mark.asyncio
@pytest.mark.parametrize("validate_queries", (True, False))
async def test_enabling_query_validation(validate_queries, mocker):
    extension_mock = mocker.Mock()
    extension_mock.get_results.return_value = {}

    extension_class_mock = mocker.Mock(return_value=extension_mock)

    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(
        query=Query,
        extensions=[extension_class_mock],
    )

    query = """
        query {
            example
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
        validate_queries=validate_queries,
    )

    assert not result.errors

    assert extension_mock.on_validation_start.called is validate_queries
    assert extension_mock.on_validation_end.called is validate_queries


@pytest.mark.asyncio
async def test_invalid_query_with_validation_disabled():
    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = await schema.execute(query, root_value=Query())

    assert str(result.errors[0]) == (
        "Syntax Error: Expected Name, found <EOF>.\n\n"
        "GraphQL request:4:5\n"
        "3 |             example\n"
        "4 |     \n"
        "  |     ^"
    )


@pytest.mark.asyncio
async def test_asking_for_wrong_field():
    @strawberry.type
    class Query:
        example: Optional[str] = None

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            sample
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
        validate_queries=False,
    )

    assert result.errors is None
    assert result.data == {}


@pytest.mark.asyncio
async def test_sending_wrong_variables():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, value: str) -> int:
            return 1

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example(value: 123)
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
        validate_queries=False,
    )

    assert (
        str(result.errors[0])
        == textwrap.dedent(
            """
            Argument 'value' has invalid value 123.

            GraphQL request:3:28
            2 |         query {
            3 |             example(value: 123)
              |                            ^
            4 |         }
            """
        ).strip()
    )


@pytest.mark.asyncio
async def test_logging_exceptions(caplog):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> int:
            raise ValueError("test")

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert len(result.errors) == 1

    # Exception was logged
    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.levelname == "ERROR"
    assert record.message == "test"
    assert record.name == "strawberry.execution"
    assert record.exc_info[0] is ValueError


@pytest.mark.asyncio
async def test_logging_graphql_exceptions(caplog):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> int:
            return None  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert len(result.errors) == 1

    # Exception was logged
    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.levelname == "ERROR"
    assert record.name == "strawberry.execution"
    assert record.exc_info[0] is TypeError


def test_overriding_process_errors(caplog):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> int:
            return None  # type: ignore

    execution_errors = []

    class CustomSchema(strawberry.Schema):
        def process_errors(self, errors, execution_context):
            nonlocal execution_errors
            execution_errors = errors

    schema = CustomSchema(query=Query)

    query = """
        query {
            example
        }
    """

    result = schema.execute_sync(
        query,
        root_value=Query(),
    )

    assert len(result.errors) == 1
    assert len(execution_errors) == 1
    assert result.errors == execution_errors

    # Exception wasn't logged
    assert len(caplog.records) == 0


def test_adding_custom_validation_rules():
    @strawberry.type
    class Query:
        example: Optional[str] = None
        another_example: Optional[str] = None

    schema = strawberry.Schema(query=Query)

    class CustomRule(ValidationRule):
        def enter_field(self, node, *args) -> None:
            if node.name.value == "example":
                self.report_error(GraphQLError("Can't query field 'example'"))

    result = schema.execute_sync(
        "{ example }",
        validation_rules=(default_validation_rules + [CustomRule]),
        root_value=Query(),
    )

    assert str(result.errors[0]) == "Can't query field 'example'"

    result = schema.execute_sync(
        "{ anotherExample }",
        validation_rules=(default_validation_rules + [CustomRule]),
        root_value=Query(),
    )
    assert not result.errors

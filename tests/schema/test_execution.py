import textwrap
from textwrap import dedent
from unittest.mock import patch

import pytest
from graphql import GraphQLError, ValidationRule, validate

import strawberry
from strawberry.extensions import (
    AddValidationRules,
    DisableValidation,
    SchemaExtension,
)
from strawberry.utils import IS_GQL_32


@pytest.mark.parametrize("validate_queries", [True, False])
@patch("strawberry.schema.schema.validate", wraps=validate)
def test_enabling_query_validation_sync(mock_validate, validate_queries):
    @strawberry.type
    class Query:
        example: str | None = None

    extensions: list[type[SchemaExtension]] = []
    if validate_queries is False:
        extensions.append(DisableValidation)

    schema = strawberry.Schema(
        query=Query,
        extensions=extensions,
    )

    query = """
        query {
            example
        }
    """

    result = schema.execute_sync(
        query,
        root_value=Query(),
    )

    assert not result.errors

    assert mock_validate.called is validate_queries


@pytest.mark.asyncio
@pytest.mark.parametrize("validate_queries", [True, False])
async def test_enabling_query_validation(validate_queries):
    @strawberry.type
    class Query:
        example: str | None = None

    extensions: list[type[SchemaExtension]] = []
    if validate_queries is False:
        extensions.append(DisableValidation)

    schema = strawberry.Schema(
        query=Query,
        extensions=extensions,
    )

    query = """
        query {
            example
        }
    """

    with patch("strawberry.schema.schema.validate", wraps=validate) as mock_validate:
        result = await schema.execute(
            query,
            root_value=Query(),
        )

        assert not result.errors

        assert mock_validate.called is validate_queries


@pytest.mark.asyncio
async def test_invalid_query_with_validation_enabled():
    @strawberry.type
    class Query:
        example: str | None = None

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
        example: str | None = None

    schema = strawberry.Schema(query=Query, extensions=[DisableValidation])

    query = """
        query {
            sample
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
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

    schema = strawberry.Schema(query=Query, extensions=[DisableValidation])

    query = """
        query {
            example(value: 123)
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    expected_error = (
        """
        Argument 'value' has invalid value 123.

        GraphQL request:3:28
        2 |         query {
        3 |             example(value: 123)
          |                            ^
        4 |         }
        """
        if IS_GQL_32
        else """
        Argument 'value' has invalid value: String cannot represent a non string value: 123

        GraphQL request:3:28
        2 |         query {
        3 |             example(value: 123)
          |                            ^
        4 |         }
        """
    )
    assert str(result.errors[0]) == textwrap.dedent(expected_error).strip()


@pytest.mark.asyncio
async def test_logging_exceptions(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> int:
            raise ValueError("test")

    schema = strawberry.Schema(query=Query)

    query = dedent(
        """
        query {
            example
        }
    """
    ).strip()

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert result.errors
    assert len(result.errors) == 1

    # Exception was logged
    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.levelname == "ERROR"
    assert (
        record.message
        == dedent(
            """
        test

        GraphQL request:2:5
        1 | query {
        2 |     example
          |     ^
        3 | }
    """
        ).strip()
    )
    assert record.name == "strawberry.execution"
    assert record.exc_info[0] is ValueError


@pytest.mark.asyncio
async def test_logging_graphql_exceptions(caplog: pytest.LogCaptureFixture):
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


@pytest.mark.asyncio
async def test_logging_parsing_error(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert result.errors
    assert len(result.errors) == 1

    # Exception was logged
    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.levelname == "ERROR"
    assert record.name == "strawberry.execution"
    assert "Syntax Error" in record.message


def test_logging_parsing_error_sync(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
    """

    result = schema.execute_sync(
        query,
        root_value=Query(),
    )

    assert result.errors
    assert len(result.errors) == 1

    # Exception was logged
    assert len(caplog.records) == 1
    record = caplog.records[0]

    assert record.levelname == "ERROR"
    assert record.name == "strawberry.execution"
    assert "Syntax Error" in record.message


@pytest.mark.asyncio
async def test_logging_validation_errors(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example {
                foo
            }
            missingField
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
    )

    assert result.errors
    assert len(result.errors) == 2

    # Exception was logged
    assert len(caplog.records) == 2
    record1 = caplog.records[0]
    assert record1.levelname == "ERROR"
    assert record1.name == "strawberry.execution"
    assert "Field 'example' must not have a selection" in record1.message

    record2 = caplog.records[1]
    assert record2.levelname == "ERROR"
    assert record2.name == "strawberry.execution"
    assert "Cannot query field 'missingField'" in record2.message


def test_logging_validation_errors_sync(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "hi"

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example {
                foo
            }
            missingField
        }
    """

    result = schema.execute_sync(
        query,
        root_value=Query(),
    )

    assert result.errors
    assert len(result.errors) == 2

    # Exception was logged
    assert len(caplog.records) == 2
    record1 = caplog.records[0]
    assert record1.levelname == "ERROR"
    assert record1.name == "strawberry.execution"
    assert "Field 'example' must not have a selection" in record1.message

    record2 = caplog.records[1]
    assert record2.levelname == "ERROR"
    assert record2.name == "strawberry.execution"
    assert "Cannot query field 'missingField'" in record2.message


def test_overriding_process_errors(caplog: pytest.LogCaptureFixture):
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
    assert caplog.records == []


def test_custom_logger(caplog: pytest.LogCaptureFixture):
    @strawberry.type
    class Query:
        example: str = "hi"

    logged_errors = []

    class CustomLogger:
        def error(self, error, execution_context=None):
            logged_errors.append((error, execution_context))

    schema = strawberry.Schema(query=Query, logger=CustomLogger())

    result = schema.execute_sync("{ missingField }")

    assert result.errors
    assert len(logged_errors) == 1
    assert logged_errors[0][0] is result.errors[0]
    assert logged_errors[0][1] is not None
    assert logged_errors[0][1].schema is schema
    assert caplog.records == []


def test_adding_custom_validation_rules():
    @strawberry.type
    class Query:
        example: str | None = None
        another_example: str | None = None

    class CustomRule(ValidationRule):
        def enter_field(self, node, *args: str) -> None:
            if node.name.value == "example":
                self.report_error(GraphQLError("Can't query field 'example'"))

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            lambda: AddValidationRules([CustomRule]),
        ],
    )

    result = schema.execute_sync(
        "{ example }",
        root_value=Query(),
    )

    assert str(result.errors[0]) == "Can't query field 'example'"

    result = schema.execute_sync(
        "{ anotherExample }",
        root_value=Query(),
    )
    assert not result.errors


def test_partial_responses():
    @strawberry.type
    class Query:
        @strawberry.field
        def example(self) -> str:
            return "hi"

        @strawberry.field
        def this_fails(self) -> str | None:
            raise ValueError("this field fails")

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
            thisFails
        }
    """

    result = schema.execute_sync(query)

    assert result.data == {"example": "hi", "thisFails": None}
    assert result.errors
    assert result.errors[0].message == "this field fails"

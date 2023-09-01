import textwrap
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional
from unittest.mock import patch

import pytest
from graphql import (
    FieldNode,
    GraphQLError,
    SourceLocation,
    ValidationRule,
    located_error,
    validate,
)

import strawberry
from strawberry.extensions import AddValidationRules, DisableValidation


@pytest.mark.parametrize("validate_queries", (True, False))
@patch("strawberry.schema.execute.validate", wraps=validate)
def test_enabling_query_validation_sync(mock_validate, validate_queries):
    @strawberry.type
    class Query:
        example: Optional[str] = None

    extensions = []
    if validate_queries is False:
        extensions.append(DisableValidation())

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
@pytest.mark.parametrize("validate_queries", (True, False))
async def test_enabling_query_validation(validate_queries):
    @strawberry.type
    class Query:
        example: Optional[str] = None

    extensions = []
    if validate_queries is False:
        extensions.append(DisableValidation())

    schema = strawberry.Schema(
        query=Query,
        extensions=extensions,
    )

    query = """
        query {
            example
        }
    """

    with patch("strawberry.schema.execute.validate", wraps=validate) as mock_validate:
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

    schema = strawberry.Schema(query=Query, extensions=[DisableValidation()])

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

    schema = strawberry.Schema(query=Query, extensions=[DisableValidation()])

    query = """
        query {
            example(value: 123)
        }
    """

    result = await schema.execute(
        query,
        root_value=Query(),
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
    @dataclass
    class Context:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def example(self, info) -> int:
            info.context.partial_errors.append(Exception("Manual exception"))
            return None  # type: ignore

    schema = strawberry.Schema(query=Query)

    query = """
        query {
            example
        }
    """

    result = await schema.execute(query, root_value=Query(), context_value=Context())

    assert len(result.errors) == 2

    # Exception was logged
    assert len(caplog.records) == 2
    record0 = caplog.records[0]

    assert record0.levelname == "ERROR"
    assert record0.name == "strawberry.execution"
    assert record0.exc_info[0] is TypeError

    record1 = caplog.records[1]

    assert record1.levelname == "ERROR"
    assert record1.name == "strawberry.execution"
    assert record1.exc_info[0] is Exception


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


def test_adding_custom_validation_rules():
    @strawberry.type
    class Query:
        example: Optional[str] = None
        another_example: Optional[str] = None

    class CustomRule(ValidationRule):
        def enter_field(self, node, *args: str) -> None:
            if node.name.value == "example":
                self.report_error(GraphQLError("Can't query field 'example'"))

    schema = strawberry.Schema(
        query=Query,
        extensions=[
            AddValidationRules([CustomRule]),
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
        def this_fails(self) -> Optional[str]:
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


def test_partial_errors_yes_data_no_errors():
    @dataclass
    class Context:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info, id: strawberry.ID) -> strawberry.ID:
            return id

    id = "12345"
    schema = strawberry.Schema(Query)
    result = schema.execute_sync(
        "query ($id: ID!) { id(id: $id) }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data["id"] == id
    assert errors is None


def test_partial_errors_no_data_yes_errors():
    @dataclass
    class Context:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info) -> strawberry.ID:
            raise Exception("Failure")

    id = "12345"
    schema = strawberry.Schema(Query)
    result = schema.execute_sync(
        "query { id }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data is None
    assert len(errors) == 1
    error: GraphQLError = errors[0]
    assert error.message == "Failure"
    assert error.locations == [SourceLocation(line=1, column=9)]
    assert error.path == ["id"]
    assert len(error.nodes) == 1
    assert isinstance(error.nodes[0], FieldNode)
    assert error.positions == [8]
    assert error.extensions == {}
    assert isinstance(error.original_error, Exception)
    assert str(error.original_error) == "Failure"
    # the actual json in the response
    assert error.formatted == {
        "message": "Failure",
        "locations": [{"line": 1, "column": 9}],
        "path": ["id"],
    }


def test_partial_errors_yes_data_yes_errors():
    @dataclass
    class Context:
        pass

    @strawberry.type
    class Query:
        @strawberry.field
        def id(self, info, id: strawberry.ID) -> strawberry.ID:
            nodes = [next(n for n in info.field_nodes if n.name.value == "id")]
            info.context.partial_errors.extend(
                [
                    Exception("Raw Exception"),
                    located_error(
                        Exception("Located error"),
                        nodes=nodes,
                        path=info.path.as_list(),
                    ),
                    located_error(Exception("Located error without any location data")),
                    GraphQLError(
                        "Raw GraphQLError with extensions", extensions={"foo": "bar"}
                    ),
                ],
            )
            return id

    id = "12345"
    schema = strawberry.Schema(Query)
    result = schema.execute_sync(
        "query ($id: ID!) { id(id: $id) }",
        variable_values={"id": id},
        context_value=Context(),
    )
    data, errors = result.data, result.errors

    assert data["id"] == id

    assert len(errors) == 4

    error0: GraphQLError = errors[0]
    assert error0.message == "Raw Exception"
    assert error0.locations is None
    assert error0.path is None
    assert error0.nodes is None
    assert error0.positions is None
    assert error0.extensions == {}
    assert isinstance(error0.original_error, Exception)
    assert str(error0.original_error) == "Raw Exception"
    # the actual json in the response
    assert error0.formatted == {
        "message": "Raw Exception",
    }

    error1: GraphQLError = errors[1]
    assert error1.message == "Located error"
    assert error1.locations == [SourceLocation(line=1, column=20)]
    assert error1.path == ["id"]
    assert len(error1.nodes) == 1
    assert isinstance(error1.nodes[0], FieldNode)
    assert error1.positions == [19]
    assert error1.extensions == {}
    assert isinstance(error1.original_error, Exception)
    assert str(error1.original_error) == "Located error"
    # the actual json in the response
    assert error1.formatted == {
        "message": "Located error",
        "locations": [{"line": 1, "column": 20}],
        "path": ["id"],
    }

    error2: GraphQLError = errors[2]
    assert error2.message == "Located error without any location data"
    assert error2.locations is None
    assert error2.path is None
    assert error2.nodes is None
    assert error2.positions is None
    assert error2.extensions == {}
    assert isinstance(error2.original_error, Exception)
    assert str(error2.original_error) == "Located error without any location data"
    # the actual json in the response
    assert error2.formatted == {
        "message": "Located error without any location data",
    }

    error3: GraphQLError = errors[3]
    assert error3.message == "Raw GraphQLError with extensions"
    assert error3.locations is None
    assert error3.path is None
    assert error3.nodes is None
    assert error3.positions is None
    assert error3.extensions == {"foo": "bar"}
    assert error3.original_error is None
    # the actual json in the response
    assert error3.formatted == {
        "message": "Raw GraphQLError with extensions",
        "extensions": {"foo": "bar"},
    }

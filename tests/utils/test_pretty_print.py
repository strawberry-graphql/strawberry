import io
from decimal import Decimal

from strawberry.types.execution import ExecutionContext, ExecutionResult
from strawberry.utils.debug import (
    pretty_print_graphql,
    pretty_print_graphql_execution_context,
    pretty_print_graphql_execution_result,
    pretty_print_graphql_operation,
)


def test_pretty_print(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation("Example", "{ query }", variables={})

    mock.assert_called_with("{ \x1b[38;5;125mquery\x1b[39m }\n")


def test_pretty_print_variables(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation("Example", "{ query }", variables={"example": 1})

    mock.assert_called_with(
        '{\n    \x1b[38;5;28;01m"example"\x1b[39;00m: \x1b[38;5;241m1\x1b[39m\n}\n'
    )


def test_pretty_print_variables_object(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation(
        "Example", "{ query }", variables={"example": Decimal(1)}
    )

    mock.assert_called_with(
        '{\n    \x1b[38;5;28;01m"example"\x1b[39;00m: '
        "\x1b[38;5;124m\"Decimal('1')\"\x1b[39m\n}\n"
    )


def test_pretty_print_graphql_execution_context(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_execution_context(
        "Example", "{ query }", variables={"example": 3}
    )

    mock.assert_called_with(
        '{\n    \x1b[38;5;28;01m"example"\x1b[39;00m: \x1b[38;5;241m3\x1b[39m\n}\n'
    )


def test_pretty_print_graphql_execution_result(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_execution_result(data=None, errors=[])

    mock.assert_called_with(
        '{\n    \x1b[38;5;28;01m"data"\x1b[39;00m: \x1b[38;5;28;01mnull\x1b[39;00m\n}'
    )


def test_pretty_print_graphql_stream():

    execution_context = ExecutionContext(
        operation_name="Example", query="{ query }", variables={"example": Decimal(1)}
    )

    execution_result = ExecutionResult(
        data=None,
        errors=[],
    )

    test_stream = io.StringIO()

    pretty_print_graphql(execution_context, execution_result, stream=test_stream)

    assert test_stream.getvalue() == (
        "Example\n{ \x1b[38;5;125mquery\x1b[39m }\n\n{\n    \x1b"
        '[38;5;28;01m"example"\x1b[39;00m: \x1b[38;5;124m"Decimal(\'1\')"'
        '\x1b[39m\n}\n\n{\n    \x1b[38;5;28;01m"data"\x1b'
        "[39;00m: \x1b[38;5;28;01mnull\x1b[39;00m\n}\n"
    )

    test_stream.close()

from decimal import Decimal

from strawberry.utils.debug import pretty_print_graphql_operation


def test_pretty_print(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation("Example", "{ query }", variables={})

    mock.assert_called_with("{ \x1b[38;5;125mquery\x1b[39m }\n")


def test_pretty_print_variables(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation("Example", "{ query }", variables={"example": 1})

    mock.assert_called_with(
        "{\n\x1b[38;5;250m    "
        '\x1b[39m\x1b[38;5;28;01m"example"\x1b[39;00m:\x1b[38;5;250m '
        "\x1b[39m\x1b[38;5;241m1\x1b[39m\n}\n"
    )


def test_pretty_print_variables_object(mocker):
    mock = mocker.patch("builtins.print")

    pretty_print_graphql_operation(
        "Example", "{ query }", variables={"example": Decimal(1)}
    )

    mock.assert_called_with(
        "{\n\x1b[38;5;250m    "
        '\x1b[39m\x1b[38;5;28;01m"example"\x1b[39;00m:\x1b[38;5;250m '
        "\x1b[39m\x1b[38;5;124m\"Decimal('1')\"\x1b[39m\n}\n"
    )

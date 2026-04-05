from libcst.codemod import CodemodTest

from strawberry.codemods.update_relay_imports import UpdateRelayImportsCodemod


class TestUpdateRelayImportsCodemod(CodemodTest):
    TRANSFORM = UpdateRelayImportsCodemod

    def test_from_relay_import_connection(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay import Connection
            """,
            """
            from strawberry.pagination import Connection
            """,
        )

    def test_from_relay_import_multiple_pagination_symbols(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay import Connection, ListConnection, connection
            """,
            """
            from strawberry.pagination import Connection, ListConnection, connection
            """,
        )

    def test_from_relay_import_mixed(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay import Connection, Node, GlobalID
            """,
            """
            from strawberry.relay import Node, GlobalID
            from strawberry.pagination import Connection
            """,
        )

    def test_from_relay_import_only_relay_symbols(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay import Node, GlobalID
            """,
            """
            from strawberry.relay import Node, GlobalID
            """,
        )

    def test_from_relay_types_import(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay.types import Connection, Edge
            """,
            """
            from strawberry.pagination.types import Connection, Edge
            """,
        )

    def test_from_relay_fields_import(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay.fields import ConnectionExtension, connection
            """,
            """
            from strawberry.pagination.fields import ConnectionExtension, connection
            """,
        )

    def test_from_relay_utils_import(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay.utils import from_base64, to_base64
            """,
            """
            from strawberry.pagination.utils import from_base64, to_base64
            """,
        )

    def test_relay_max_results_renamed(self) -> None:
        self.assertCodemod(
            """
            from strawberry.schema.config import StrawberryConfig
            config = StrawberryConfig(relay_max_results=50)
            """,
            """
            from strawberry.schema.config import StrawberryConfig
            config = StrawberryConfig(connection_max_results=50)
            """,
        )

    def test_relay_max_results_with_other_args(self) -> None:
        self.assertCodemod(
            """
            from strawberry.schema.config import StrawberryConfig
            config = StrawberryConfig(auto_camel_case=True, relay_max_results=100)
            """,
            """
            from strawberry.schema.config import StrawberryConfig
            config = StrawberryConfig(auto_camel_case=True, connection_max_results=100)
            """,
        )

    def test_from_relay_import_with_alias(self) -> None:
        self.assertCodemod(
            """
            from strawberry.relay import Connection as Conn
            """,
            """
            from strawberry.pagination import Connection as Conn
            """,
        )

    def test_no_changes_for_unrelated_code(self) -> None:
        self.assertCodemod(
            """
            from strawberry import relay
            from strawberry.types import Info
            """,
            """
            from strawberry import relay
            from strawberry.types import Info
            """,
        )

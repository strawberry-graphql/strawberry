from libcst.codemod import CodemodTest

from strawberry.codemods.replace_scalar_wrappers import ReplaceScalarWrappers


class TestReplaceScalarWrappers(CodemodTest):
    TRANSFORM = ReplaceScalarWrappers

    def test_replace_date(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Date

            field: Date
        """

        after = """
            import datetime

            field: datetime.date
        """

        self.assertCodemod(before, after)

    def test_replace_datetime(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import DateTime

            field: DateTime
        """

        after = """
            import datetime

            field: datetime.datetime
        """

        self.assertCodemod(before, after)

    def test_replace_time(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Time

            field: Time
        """

        after = """
            import datetime

            field: datetime.time
        """

        self.assertCodemod(before, after)

    def test_replace_decimal(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Decimal

            field: Decimal
        """

        after = """
            from decimal import Decimal

            field: Decimal
        """

        self.assertCodemod(before, after)

    def test_replace_uuid(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import UUID

            field: UUID
        """

        after = """
            from uuid import UUID

            field: UUID
        """

        self.assertCodemod(before, after)

    def test_replace_multiple_scalars(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Date, DateTime, UUID

            date_field: Date
            datetime_field: DateTime
            uuid_field: UUID
        """

        after = """
            import datetime
            from uuid import UUID

            date_field: datetime.date
            datetime_field: datetime.datetime
            uuid_field: UUID
        """

        self.assertCodemod(before, after)

    def test_preserve_other_imports(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Date, DateDefinition

            field: Date
        """

        after = """
            from strawberry.schema.types.base_scalars import DateDefinition
            import datetime

            field: datetime.date
        """

        self.assertCodemod(before, after)

    def test_no_changes_when_no_scalar_imports(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import DateDefinition

            definition = DateDefinition
        """

        after = """
            from strawberry.schema.types.base_scalars import DateDefinition

            definition = DateDefinition
        """

        self.assertCodemod(before, after)

    def test_replace_aliased_import(self) -> None:
        before = """
            from strawberry.schema.types.base_scalars import Date as MyDate

            field: MyDate
        """

        after = """
            import datetime

            field: datetime.date
        """

        self.assertCodemod(before, after)

    def test_imported_but_unused_scalar(self) -> None:
        """Test behavior when a scalar is imported but not used.

        The codemod adds replacement imports for all imported scalars,
        even if they're not used. Removing unused imports is a separate
        concern that tools like ruff or autoflake can handle.
        """
        before = """
            from strawberry.schema.types.base_scalars import Date, UUID

            field: Date
        """

        # Both datetime and uuid imports are added since both were imported
        after = """
            import datetime
            from uuid import UUID

            field: datetime.date
        """

        self.assertCodemod(before, after)

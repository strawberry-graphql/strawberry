from libcst.codemod import CodemodTest

from strawberry.codemods.update_imports import UpdateImportsCodemod


class TestConvertConstantCommand(CodemodTest):
    TRANSFORM = UpdateImportsCodemod

    def test_update_field(self) -> None:
        before = """
            from strawberry.field import something
        """

        after = """
            from strawberry.types.field import something
        """

        self.assertCodemod(before, after)

    def test_update_import_strawberry_type(self) -> None:
        before = """
            from strawberry.type import (
                StrawberryContainer,
                StrawberryList,
                StrawberryOptional,
                StrawberryType,
                WithStrawberryObjectDefinition,
            )
        """

        after = """
            from strawberry.types.base import (
                StrawberryContainer,
                StrawberryList,
                StrawberryOptional,
                StrawberryType,
                WithStrawberryObjectDefinition,
            )
        """

        self.assertCodemod(before, after)

    def test_update_import_strawberry_type_object_definition(self) -> None:
        before = """
            from strawberry.type import (
                StrawberryContainer,
                StrawberryList,
                StrawberryOptional,
                StrawberryType,
                WithStrawberryObjectDefinition,
                get_object_definition,
            )
        """

        after = """
            from strawberry.types.base import (
                StrawberryContainer,
                StrawberryList,
                StrawberryOptional,
                StrawberryType,
                WithStrawberryObjectDefinition)
            from strawberry.types import get_object_definition
        """

        self.assertCodemod(before, after)

    def test_update_import_strawberry_type_object_definition_only(self) -> None:
        before = """
            from strawberry.type import get_object_definition
        """

        after = """
            from strawberry.types import get_object_definition
        """

        self.assertCodemod(before, after)

    def test_update_import_union(self) -> None:
        before = """
            from strawberry.union import StrawberryUnion
        """

        after = """
            from strawberry.types.union import StrawberryUnion
        """

        self.assertCodemod(before, after)

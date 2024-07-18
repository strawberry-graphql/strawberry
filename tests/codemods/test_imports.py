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
                has_object_definition,
            )
        """

        after = """
            from strawberry.types.base import (
                StrawberryContainer,
                StrawberryList,
                StrawberryOptional,
                StrawberryType,
                WithStrawberryObjectDefinition)
            from strawberry.types import get_object_definition, has_object_definition
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

    def test_update_import_auto(self) -> None:
        before = """
            from strawberry.auto import auto
        """

        after = """
            from strawberry.types.auto import auto
        """

        self.assertCodemod(before, after)

    def test_update_import_unset(self) -> None:
        before = """
            from strawberry.unset import UNSET
        """

        after = """
            from strawberry.types.unset import UNSET
        """

        self.assertCodemod(before, after)

    def test_update_import_arguments(self) -> None:
        before = """
            from strawberry.arguments import StrawberryArgument
        """

        after = """
            from strawberry.types.arguments import StrawberryArgument
        """

        self.assertCodemod(before, after)

    def test_update_import_lazy_type(self) -> None:
        before = """
            from strawberry.lazy_type import LazyType
        """

        after = """
            from strawberry.types.lazy_type import LazyType
        """

        self.assertCodemod(before, after)

    def test_update_import_object_type(self) -> None:
        before = """
            from strawberry.object_type import StrawberryObjectDefinition
        """

        after = """
            from strawberry.types.object_type import StrawberryObjectDefinition
        """

        self.assertCodemod(before, after)

    def test_update_import_enum(self) -> None:
        before = """
            from strawberry.enum import StrawberryEnum
        """

        after = """
            from strawberry.types.enum import StrawberryEnum
        """

        self.assertCodemod(before, after)

    def test_update_types_types(self) -> None:
        before = """
            from strawberry.types.types import StrawberryObjectDefinition
        """

        after = """
            from strawberry.types.base import StrawberryObjectDefinition
        """

        self.assertCodemod(before, after)

    def test_update_is_private(self) -> None:
        before = """
            from strawberry.private import is_private
        """

        after = """
            from strawberry.types.private import is_private
        """

        self.assertCodemod(before, after)

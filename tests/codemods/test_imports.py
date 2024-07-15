from libcst.codemod import CodemodTest

from strawberry.codemods.update_imports import UpdateImportsCodemod


class TestConvertConstantCommand(CodemodTest):
    TRANSFORM = UpdateImportsCodemod

    def test_update_union(self) -> None:
        before = """
            from strawberry.field import something
        """

        after = """
            from strawberry.types.field import something
        """

        self.assertCodemod(before, after)

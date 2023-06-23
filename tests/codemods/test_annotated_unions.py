from libcst.codemod import CodemodTest

from strawberry.codemods.annotated_unions import ConvertUnionToAnnotatedUnion

# TODO: Annotated from?
# TODO: pipe


class TestConvertConstantCommand(CodemodTest):
    # The codemod that will be instantiated for us in assertCodemod.
    TRANSFORM = ConvertUnionToAnnotatedUnion

    def test_update_union(self) -> None:
        before = """
            AUnion = strawberry.union(name="ABC", types=(Foo, Bar))
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.type(name="ABC")]
        """

        self.assertCodemod(before, after)

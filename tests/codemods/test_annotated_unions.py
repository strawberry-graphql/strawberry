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

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_update_union_using_import(self) -> None:
        before = """
            from strawberry import union

            AUnion = union(name="ABC", types=(Foo, Bar))
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_update_union_positional_name(self) -> None:
        before = """
            AUnion = strawberry.union("ABC", types=(Foo, Bar))
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_update_swapped_kwargs(self) -> None:
        before = """
            AUnion = strawberry.union(types=(Foo, Bar), name="ABC")
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_update_union_list(self) -> None:
        before = """
            AUnion = strawberry.union(name="ABC", types=[Foo, Bar])
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_update_positional_arguments(self) -> None:
        before = """
            AUnion = strawberry.union("ABC", (Foo, Bar))
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

    def test_supports_directives_and_description(self) -> None:
        before = """
            AUnion = strawberry.union(
                "ABC",
                (Foo, Bar),
                description="cool union",
                directives=[object()],
            )
        """

        after = """
            from typing_extensions import Annotated

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC", description="cool union", directives=[object()])]
        """

        self.assertCodemod(before, after)

    def test_noop_with_annotated_unions(self) -> None:
        before = """
            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        after = """
            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after)

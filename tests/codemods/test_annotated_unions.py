from libcst.codemod import CodemodTest

from strawberry.codemods.annotated_unions import ConvertUnionToAnnotatedUnion


class TestConvertConstantCommand(CodemodTest):
    TRANSFORM = ConvertUnionToAnnotatedUnion

    def test_update_union(self) -> None:
        before = """
            AUnion = strawberry.union(name="ABC", types=(Foo, Bar))
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(
            before, after, use_pipe_syntax=False, use_typing_extensions=False
        )

    def test_update_union_typing_extensions(self) -> None:
        before = """
            AUnion = strawberry.union(name="ABC", types=(Foo, Bar))
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_update_union_using_import(self) -> None:
        before = """
            from strawberry import union

            AUnion = union(name="ABC", types=(Foo, Bar))
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_noop_other_union(self) -> None:
        before = """
            from potato import union

            union("A", "B")
        """

        after = """
            from potato import union

            union("A", "B")
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_update_union_positional_name(self) -> None:
        before = """
            AUnion = strawberry.union("ABC", types=(Foo, Bar))
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_update_swapped_kwargs(self) -> None:
        before = """
            AUnion = strawberry.union(types=(Foo, Bar), name="ABC")
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_update_union_list(self) -> None:
        before = """
            AUnion = strawberry.union(name="ABC", types=[Foo, Bar])
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_update_positional_arguments(self) -> None:
        before = """
            AUnion = strawberry.union("ABC", (Foo, Bar))
        """

        after = """
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

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
            from typing import Annotated, Union

            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC", description="cool union", directives=[object()])]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_noop_with_annotated_unions(self) -> None:
        before = """
            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        after = """
            AUnion = Annotated[Union[Foo, Bar], strawberry.union(name="ABC")]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

from libcst.codemod import CodemodTest

from strawberry.codemods.maybe_optional import ConvertMaybeToOptional


class TestConvertMaybeToOptional(CodemodTest):
    TRANSFORM = ConvertMaybeToOptional

    def test_simple_maybe(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[str]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[str | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_simple_maybe_union_syntax(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[str]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[Union[str, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_strawberry_maybe(self) -> None:
        before = """
            import strawberry

            field: strawberry.Maybe[int]
        """

        after = """
            import strawberry

            field: strawberry.Maybe[int | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_nested_type(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[List[str]]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[List[str] | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_already_has_none_pipe(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[str | None]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[str | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_already_has_none_union(self) -> None:
        before = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[str, None]]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[str, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_multiple_maybe_fields(self) -> None:
        before = """
            from strawberry import Maybe

            @strawberry.type
            class User:
                name: Maybe[str]
                age: Maybe[int]
                email: Maybe[str]
        """

        after = """
            from strawberry import Maybe

            @strawberry.type
            class User:
                name: Maybe[str | None]
                age: Maybe[int | None]
                email: Maybe[str | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_function_annotation(self) -> None:
        before = """
            from strawberry import Maybe

            def get_user() -> Maybe[User]:
                return None
        """

        after = """
            from strawberry import Maybe

            def get_user() -> Maybe[User | None]:
                return None
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_generic_type(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[Dict[str, Any]]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[Dict[str, Any] | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

    def test_union_type_inside_maybe(self) -> None:
        before = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[str, int]]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[str, int] | None]
        """

        self.assertCodemod(before, after, use_pipe_syntax=True)

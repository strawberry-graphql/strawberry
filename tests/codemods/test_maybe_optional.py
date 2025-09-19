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
            from typing import Union

            field: Maybe[Union[str, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_simple_maybe_union_syntax(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[str]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

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
            from typing import Union

            field: strawberry.Maybe[Union[int, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_nested_type(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[List[str]]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[List[str], None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_already_has_none_pipe(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[Union[str, None]]
        """

        after = """
            from strawberry import Maybe

            field: Maybe[Union[str, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

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

        self.assertCodemod(before, after, use_pipe_syntax=False)

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
            from typing import Union

            @strawberry.type
            class User:
                name: Maybe[Union[str, None]]
                age: Maybe[Union[int, None]]
                email: Maybe[Union[str, None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_function_annotation(self) -> None:
        before = """
            from strawberry import Maybe

            def get_user() -> Maybe[User]:
                return None
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            def get_user() -> Maybe[Union[User, None]]:
                return None
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_generic_type(self) -> None:
        before = """
            from strawberry import Maybe

            field: Maybe[Dict[str, Any]]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[Dict[str, Any], None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

    def test_union_type_inside_maybe(self) -> None:
        before = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[str, int]]
        """

        after = """
            from strawberry import Maybe
            from typing import Union

            field: Maybe[Union[Union[str, int], None]]
        """

        self.assertCodemod(before, after, use_pipe_syntax=False)

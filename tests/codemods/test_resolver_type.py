from libcst.codemod import CodemodTest

from strawberry.codemods.resolver_type import ConvertFieldWithResolverTypeAnnotations


class TestConvertConstantCommand(CodemodTest):
    TRANSFORM = ConvertFieldWithResolverTypeAnnotations

    def test_update_annotation(self) -> None:
        before = """
            class User:
                name: str = strawberry.field(description="Name")
                age: int = strawberry.field(resolver=get_user_age)
                mut: int = strawberry.mutation(resolver=mutit)
                sub: int = strawberry.subscription(resolver=subit)
                no_ann = strawberry.field(resolver=no_annit)
        """

        after = """
            class User:
                name: str = strawberry.field(description="Name")
                age: strawberry.Resolver[int] = strawberry.field(resolver=get_user_age)
                mut: strawberry.Resolver[int] = strawberry.mutation(resolver=mutit)
                sub: strawberry.Resolver[int] = strawberry.subscription(resolver=subit)
                no_ann = strawberry.field(resolver=no_annit)
        """

        self.assertCodemod(before, after)

    def test_update_annotation_named_import(self) -> None:
        for func in ("field", "mutation", "subscription"):
            before = f"""
                from strawberry import {func}

                class User:
                    name: str = {func}(description="Name")
                    age: int = {func}(resolver=get_user_age)
            """

            after = f"""
                from strawberry import Resolver, {func}

                class User:
                    name: str = {func}(description="Name")
                    age: Resolver[int] = {func}(resolver=get_user_age)
            """

            self.assertCodemod(before, after)

    def test_noop_no_resolvers(self) -> None:
        before = """
            from strawberry import field

            class User:
                name: str = field(description="Name")
                age: int = field(deprecation_reason="some")
                no_ann = field(resolver=no_annit)
        """

        self.assertCodemod(before, before)

    def test_noop_no_annotation(self) -> None:
        before = """
            from strawberry import field

            class User:
                name = field(description="Name")
                age = field(resolver=get_user_age)
                mut = mutation(resolver=mutit)
                sub = subscription(resolver=subit)
        """

        self.assertCodemod(before, before)

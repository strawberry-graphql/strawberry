from libcst.codemod import CodemodTest

from strawberry.codemods.schema_config import ConvertStrawberryConfigToDict


class TestConvertConstantCommand(CodemodTest):
    TRANSFORM = ConvertStrawberryConfigToDict

    def test_update_config(self) -> None:
        before = """
            import strawberry
            from strawberry.schema.config import StrawberryConfig

            schema = strawberry.Schema(
                query=Query, config=StrawberryConfig(auto_camel_case=False)
            )
        """

        after = """
            import strawberry

            schema = strawberry.Schema(
                query=Query, config=dict(auto_camel_case=False)
            )
        """

        self.assertCodemod(
            before,
            after,
        )

    def test_update_config_default(self) -> None:
        before = """
            import strawberry
            from strawberry.schema.config import StrawberryConfig

            schema = strawberry.Schema(
                query=Query, config=StrawberryConfig()
            )
        """

        after = """
            import strawberry

            schema = strawberry.Schema(
                query=Query, config=dict()
            )
        """

        self.assertCodemod(
            before,
            after,
        )

    def test_update_config_with_two_args(self) -> None:
        before = """
            import strawberry
            from strawberry.schema.config import StrawberryConfig

            schema = strawberry.Schema(
                query=Query,
                config=StrawberryConfig(auto_camel_case=True, default_resolver=getitem)
            )
        """

        after = """
            import strawberry

            schema = strawberry.Schema(
                query=Query,
                config=dict(auto_camel_case=True, default_resolver=getitem)
            )
        """

        self.assertCodemod(
            before,
            after,
        )

    def test_update_config_declared_outside(self) -> None:
        before = """
            import strawberry
            from strawberry.schema.config import StrawberryConfig

            config = StrawberryConfig(auto_camel_case=True, default_resolver=getitem)

            schema = strawberry.Schema(
                query=Query,
                config=config
            )
        """

        after = """
            import strawberry

            config = dict(auto_camel_case=True, default_resolver=getitem)

            schema = strawberry.Schema(
                query=Query,
                config=config
            )
        """

        self.assertCodemod(
            before,
            after,
        )

    def test_update_config_declared_outside_not_used_in_module(self) -> None:
        before = """
            from strawberry.schema.config import StrawberryConfig

            config = StrawberryConfig(auto_camel_case=True, default_resolver=getitem)
        """

        after = """
            config = dict(auto_camel_case=True, default_resolver=getitem)
        """

        self.assertCodemod(
            before,
            after,
        )

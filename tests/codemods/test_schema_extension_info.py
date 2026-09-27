from libcst.codemod import CodemodTest

from strawberry.codemods.schema_extension_info import ConvertSchemaExtensionInfo


class TestConvertSchemaExtensionInfo(CodemodTest):
    TRANSFORM = ConvertSchemaExtensionInfo

    def test_converts_graphql_info_annotation(self) -> None:
        before = """
            from graphql import GraphQLResolveInfo
            from strawberry.extensions import SchemaExtension


            class MyExtension(SchemaExtension):
                def resolve(self, next_, root, info: GraphQLResolveInfo, **kwargs):
                    print(info.parent_type)
                    return next_(root, info, **kwargs)
        """

        after = """
            from strawberry.extensions import SchemaExtension
            import strawberry


            class MyExtension(SchemaExtension):
                def resolve(self, next_, root, strawberry_info: strawberry.Info, **kwargs):
                    info = strawberry_info._raw_info
                    print(info.parent_type)
                    return next_(root, info, **kwargs)
        """

        self.assertCodemod(before, after)

    def test_converts_unannotated_info_after_docstring(self) -> None:
        before = '''
            from strawberry.extensions import SchemaExtension


            class MyExtension(SchemaExtension):
                async def resolve(self, next_, root, info, *args, **kwargs):
                    """Resolve a field."""
                    return await next_(root, info, *args, **kwargs)
        '''

        after = '''
            from strawberry.extensions import SchemaExtension
            import strawberry


            class MyExtension(SchemaExtension):
                async def resolve(self, next_, root, strawberry_info: strawberry.Info, *args, **kwargs):
                    """Resolve a field."""
                    info = strawberry_info._raw_info
                    return await next_(root, info, *args, **kwargs)
        '''

        self.assertCodemod(before, after)

    def test_supports_aliased_imports_and_info_parameter_names(self) -> None:
        before = """
            from graphql import GraphQLResolveInfo as ResolveInfo
            from strawberry.extensions import SchemaExtension as Extension


            class MyExtension(Extension):
                def resolve(self, next_, root, execution_info: ResolveInfo, **kwargs):
                    return next_(root, execution_info, **kwargs)
        """

        after = """
            from strawberry.extensions import SchemaExtension as Extension
            import strawberry


            class MyExtension(Extension):
                def resolve(self, next_, root, strawberry_info: strawberry.Info, **kwargs):
                    execution_info = strawberry_info._raw_info
                    return next_(root, execution_info, **kwargs)
        """

        self.assertCodemod(before, after)

    def test_supports_qualified_schema_extension(self) -> None:
        before = """
            import strawberry


            class MyExtension(strawberry.extensions.SchemaExtension):
                def resolve(self, next_, root, info, **kwargs):
                    return next_(root, info, **kwargs)
        """

        after = """
            import strawberry


            class MyExtension(strawberry.extensions.SchemaExtension):
                def resolve(self, next_, root, strawberry_info: strawberry.Info, **kwargs):
                    info = strawberry_info._raw_info
                    return next_(root, info, **kwargs)
        """

        self.assertCodemod(before, after)

    def test_supports_schema_extension_defined_in_a_function(self) -> None:
        before = """
            from strawberry.extensions import SchemaExtension


            def create_extension():
                class MyExtension(SchemaExtension):
                    def resolve(self, next_, root, info, **kwargs):
                        return next_(root, info, **kwargs)

                return MyExtension
        """

        after = """
            from strawberry.extensions import SchemaExtension
            import strawberry


            def create_extension():
                class MyExtension(SchemaExtension):
                    def resolve(self, next_, root, strawberry_info: strawberry.Info, **kwargs):
                        info = strawberry_info._raw_info
                        return next_(root, info, **kwargs)

                return MyExtension
        """

        self.assertCodemod(before, after)

    def test_does_not_change_strawberry_info_extension(self) -> None:
        source = """
            import strawberry
            from strawberry.extensions import SchemaExtension


            class MyExtension(SchemaExtension):
                def resolve(self, next_, root, info: strawberry.Info, **kwargs):
                    return next_(root, info, **kwargs)
        """

        self.assertCodemod(source, source)

    def test_does_not_change_field_extensions(self) -> None:
        source = """
            from strawberry.extensions import FieldExtension


            class MyExtension(FieldExtension):
                def resolve(self, next_, root, info, **kwargs):
                    return next_(root, info, **kwargs)
        """

        self.assertCodemod(source, source)

    def test_reports_unrecognized_info_annotation(self) -> None:
        source = """
            from strawberry.extensions import SchemaExtension


            class MyExtension(SchemaExtension):
                def resolve(self, next_, root, info: CustomInfo, **kwargs):
                    return next_(root, info, **kwargs)
        """

        self.assertCodemod(
            source,
            source,
            expected_warnings=[
                (
                    "Skipped resolve: the annotation on `info` is not a recognized "
                    "graphql-core Info type."
                )
            ],
        )

import textwrap

from strawberry.schema_codegen import codegen


def test_directive_with_arguments():
    schema = """
    directive @authz(resource: String!, action: String!) on FIELD_DEFINITION

    type Query {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Authz:
            resource: str
            action: str

        @strawberry.type
        class Query:
            hello: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_without_arguments():
    schema = """
    directive @deprecated on FIELD_DEFINITION

    type Query {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Deprecated:
            pass

        @strawberry.type
        class Query:
            hello: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_with_description():
    schema = '''
    """Authorization directive for field-level access control"""
    directive @authz(resource: String!) on FIELD_DEFINITION

    type Query {
        hello: String!
    }
    '''

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION], description="Authorization directive for field-level access control")
        class Authz:
            resource: str

        @strawberry.type
        class Query:
            hello: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_with_multiple_locations():
    schema = """
    directive @example on FIELD_DEFINITION | OBJECT | INTERFACE

    type Query {
        hello: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION, Location.OBJECT, Location.INTERFACE])
        class Example:
            pass

        @strawberry.type
        class Query:
            hello: str

        schema = strawberry.Schema(query=Query)
        """
    ).strip()

    assert codegen(schema).strip() == expected

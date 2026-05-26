import textwrap

from strawberry.schema_codegen import codegen


def test_basic_directive_definition():
    schema = """
    directive @cached(maxAge: Int!) on FIELD_DEFINITION

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Cached:
            max_age: int = strawberry.directive_field(name="maxAge")

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_applied_to_input_field():
    schema = """
    directive @limits(max: Int!) on INPUT_FIELD_DEFINITION

    input CreateUserInput {
        name: String!
        tags: [String!] @limits(max: 5)
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.INPUT_FIELD_DEFINITION])
        class Limits:
            max: int

        @strawberry.input
        class CreateUserInput:
            name: str
            tags: strawberry.Maybe[list[str] | None] = strawberry.field(directives=[Limits(max=5)])
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_applied_to_output_type_field():
    schema = """
    directive @cached(maxAge: Int!) on FIELD_DEFINITION

    type User {
        name: String!
        friends: [String!]! @cached(maxAge: 60)
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Cached:
            max_age: int = strawberry.directive_field(name="maxAge")

        @strawberry.type
        class User:
            name: str
            friends: list[str] = strawberry.field(directives=[Cached(max_age=60)])
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_applied_to_type_decorator():
    schema = """
    directive @auth(role: String!) on OBJECT

    type User @auth(role: "admin") {
        id: ID!
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.OBJECT])
        class Auth:
            role: str

        @strawberry.type(directives=[Auth(role="admin")])
        class User:
            id: strawberry.ID
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_camel_case_argument_names():
    schema = """
    directive @rateLimit(maxCalls: Int!, timeWindow: String!) on FIELD_DEFINITION

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class RateLimit:
            max_calls: int = strawberry.directive_field(name="maxCalls")
            time_window: str = strawberry.directive_field(name="timeWindow")

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_with_default_values():
    schema = """
    directive @cached(maxAge: Int! = 300, scope: String! = "public") on FIELD_DEFINITION

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Cached:
            max_age: int = strawberry.directive_field(name="maxAge", default=300)
            scope: str = "public"

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_repeatable_directive():
    schema = """
    directive @label(name: String!) repeatable on OBJECT

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.OBJECT], repeatable=True)
        class Label:
            name: str

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_multiple_locations():
    schema = """
    directive @auth(role: String!) on OBJECT | FIELD_DEFINITION

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.OBJECT, Location.FIELD_DEFINITION])
        class Auth:
            role: str

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_no_arg_directive():
    schema = """
    directive @internal on FIELD_DEFINITION

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Internal:
            pass

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_multiple_directives_on_one_field():
    schema = """
    directive @cached(maxAge: Int!) on FIELD_DEFINITION
    directive @auth(role: String!) on FIELD_DEFINITION

    type User {
        friends: [String!]! @cached(maxAge: 60) @auth(role: "admin")
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Cached:
            max_age: int = strawberry.directive_field(name="maxAge")

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Auth:
            role: str

        @strawberry.type
        class User:
            friends: list[str] = strawberry.field(directives=[Cached(max_age=60), Auth(role="admin")])
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_with_description():
    schema = '''
    """Rate limiting directive"""
    directive @rateLimit(max: Int!) on FIELD_DEFINITION

    type User {
        name: String!
    }
    '''

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(description="Rate limiting directive", locations=[Location.FIELD_DEFINITION])
        class RateLimit:
            max: int

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_directive_query_only_location_skipped():
    """Directives with only execution-time locations should be skipped."""
    schema = """
    directive @log on QUERY

    type User {
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class User:
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_federation_with_non_federation_directive():
    """Federation schemas should still generate non-federation directive classes."""
    schema = """
    extend schema @link(url: "https://specs.apollo.dev/federation/v2.0", import: ["@key"])

    directive @cached(maxAge: Int!) on FIELD_DEFINITION

    type User @key(fields: "id") {
        id: ID!
        name: String! @cached(maxAge: 120)
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Cached:
            max_age: int = strawberry.directive_field(name="maxAge")

        @strawberry.federation.type(keys=["id"])
        class User:
            id: strawberry.ID
            name: str = strawberry.field(directives=[Cached(max_age=120)])
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_no_arg_directive_applied():
    """A directive with no args applied to a field generates ClassName() call."""
    schema = """
    directive @internal on FIELD_DEFINITION

    type User {
        secret: String! @internal
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from strawberry.schema_directive import Location

        @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
        class Internal:
            pass

        @strawberry.type
        class User:
            secret: str = strawberry.field(directives=[Internal()])
        """
    ).strip()

    assert codegen(schema).strip() == expected

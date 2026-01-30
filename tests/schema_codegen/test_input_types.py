import textwrap

from strawberry.schema_codegen import codegen


def test_codegen_input_type():
    schema = """
    input Example {
        a: Int!
        b: Float!
        c: Boolean!
        d: String!
        e: ID!
        f: [Int!]!
        g: [Float!]!
        h: [Boolean!]!
        i: [String!]!
        j: [ID!]!
        k: [Int]
        l: [Float]
        m: [Boolean]
        n: [String]
        o: [ID]
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Example:
            a: int
            b: float
            c: bool
            d: str
            e: strawberry.ID
            f: list[int]
            g: list[float]
            h: list[bool]
            i: list[str]
            j: list[strawberry.ID]
            k: strawberry.Maybe[list[int | None] | None]
            l: strawberry.Maybe[list[float | None] | None]
            m: strawberry.Maybe[list[bool | None] | None]
            n: strawberry.Maybe[list[str | None] | None]
            o: strawberry.Maybe[list[strawberry.ID | None] | None]
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_nullable_input_fields_use_maybe():
    """Nullable input fields should use strawberry.Maybe so they can be omitted."""
    schema = """
    input HealthResultInput {
        someNumber: Int
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class HealthResultInput:
            some_number: strawberry.Maybe[int | None]
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_mixed_required_and_nullable_input_fields():
    """Input types with both required and nullable fields generate correctly."""
    schema = """
    input MultiFieldInput {
        requiredField: String!
        optionalInt: Int
        optionalString: String
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class MultiFieldInput:
            required_field: str
            optional_int: strawberry.Maybe[int | None]
            optional_string: strawberry.Maybe[str | None]
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_nullable_input_fields_with_default_values():
    """Nullable input fields with GraphQL default values still use Maybe."""
    schema = """
    input WithDefaults {
        name: String!
        count: Int = 42
        label: String = "default"
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class WithDefaults:
            name: str
            count: strawberry.Maybe[int | None] = 42
            label: strawberry.Maybe[str | None] = "default"
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_output_type_nullable_fields_do_not_use_maybe():
    """Nullable fields on output types should use T | None, not Maybe."""
    schema = """
    type Result {
        value: Int
        name: String!
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.type
        class Result:
            value: int | None
            name: str
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_integer_default():
    schema = """
    input Config {
        retries: Int! = 3
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            retries: int = 3
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_float_default():
    schema = """
    input Config {
        rate: Float! = 1.5
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            rate: float = 1.5
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_string_default():
    schema = """
    input Config {
        name: String! = "hello"
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            name: str = "hello"
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_boolean_default():
    schema = """
    input Config {
        enabled: Boolean! = true
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            enabled: bool = True
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_null_default():
    schema = """
    input Config {
        value: String = null
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            value: strawberry.Maybe[str | None] = None
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_enum_default():
    schema = """
    enum Status {
        ACTIVE
        INACTIVE
    }

    input Config {
        status: Status! = ACTIVE
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from enum import Enum

        @strawberry.enum
        class Status(Enum):
            ACTIVE = "ACTIVE"
            INACTIVE = "INACTIVE"

        @strawberry.input
        class Config:
            status: Status = Status.ACTIVE
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_list_default():
    schema = """
    input Config {
        values: [Int!]! = [1, 2, 3]
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            values: list[int] = [1, 2, 3]
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_input_field_default_with_description():
    schema = '''
    input Config {
        """The number of retries"""
        retries: Int! = 3
    }
    '''

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class Config:
            retries: int = strawberry.field(description="The number of retries", default=3)
        """
    ).strip()

    assert codegen(schema).strip() == expected

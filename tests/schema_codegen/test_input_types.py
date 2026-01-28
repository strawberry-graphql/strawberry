import textwrap

import strawberry
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

    generated_code = codegen(schema)

    expected = textwrap.dedent(
        """
        import strawberry

        @strawberry.input
        class HealthResultInput:
            some_number: strawberry.Maybe[int | None]
        """
    ).strip()

    assert generated_code.strip() == expected


def test_nullable_input_fields_can_be_omitted():
    """Generated input types with nullable fields can be instantiated without them."""
    schema = """
    input HealthResultInput {
        someNumber: Int
    }
    """

    generated_code = codegen(schema)

    namespace = {}
    exec(generated_code, namespace)  # noqa: S102

    HealthResultInput = namespace["HealthResultInput"]

    # Nullable fields should be optional - can be omitted
    instance = HealthResultInput()
    assert instance.some_number is None


def test_mixed_required_and_nullable_input_fields():
    """Input types with both required and nullable fields work correctly."""
    schema = """
    input MultiFieldInput {
        requiredField: String!
        optionalInt: Int
        optionalString: String
    }
    """

    generated_code = codegen(schema)

    namespace = {}
    exec(generated_code, namespace)  # noqa: S102

    MultiFieldInput = namespace["MultiFieldInput"]

    # Should be able to provide only the required field
    instance = MultiFieldInput(required_field="test")

    assert instance.required_field == "test"
    assert instance.optional_int is None
    assert instance.optional_string is None


def test_maybe_fields_support_some_values():
    """Maybe fields work correctly when a value is provided via Some."""
    schema = """
    input HealthResultInput {
        someNumber: Int
    }
    """

    generated_code = codegen(schema)

    namespace = {}
    exec(generated_code, namespace)  # noqa: S102

    HealthResultInput = namespace["HealthResultInput"]

    # Provide a value - it should be wrapped in Some
    instance = HealthResultInput(some_number=strawberry.Some(42))

    assert instance.some_number is not None
    assert instance.some_number.value == 42


def test_maybe_fields_distinguish_absent_from_null():
    """Maybe fields can distinguish between absent and explicit null."""
    schema = """
    input HealthResultInput {
        someNumber: Int
    }
    """

    generated_code = codegen(schema)

    namespace = {}
    exec(generated_code, namespace)  # noqa: S102

    HealthResultInput = namespace["HealthResultInput"]

    absent_instance = HealthResultInput()
    assert absent_instance.some_number is None

    # Explicit null is represented as Some(None)
    null_instance = HealthResultInput(some_number=strawberry.Some(None))
    assert null_instance.some_number is not None
    assert null_instance.some_number.value is None

import strawberry


def upper_validator(value, info):
    if info.context and info.context in value:
        raise ValueError("Invalid value")
    return value.upper()


def test_validator():
    @strawberry.type
    class Type:
        string: str = strawberry.field(validators=[upper_validator])

    @strawberry.type
    class Query:
        @strawberry.field
        def type() -> Type:
            return Type("hello")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ type { string } }")

    assert not result.errors
    assert result.data["type"]["string"] == "HELLO"

    # error case
    result = schema.execute_sync("{ type { string } }", context_value="hello")

    assert result.errors[0].message == "Invalid value"


def test_validator_decorator():
    @strawberry.type
    class Type:
        string: str = strawberry.field()

        @string.validator
        def validator(value, info):
            return value.title()

    @strawberry.type
    class Query:
        @strawberry.field
        def type() -> Type:
            return Type("hello")

    schema = strawberry.Schema(Query)

    result = schema.execute_sync("{ type { string } }")

    assert not result.errors
    assert result.data["type"]["string"] == "Hello"


def test_input_validation():
    @strawberry.input
    class Input:
        string: str = strawberry.field(validators=[upper_validator])

    @strawberry.type
    class Query:
        s: str

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def mutation(self, input: Input) -> str:
            return input.string

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync('mutation { mutation(input: { string: "hello" }) }')

    assert not result.errors
    assert result.data["mutation"] == "HELLO"

    # error case
    result = schema.execute_sync(
        'mutation { mutation(input: { string: "hello" }) }', context_value="hello"
    )

    assert result.errors[0].message == "Invalid value"

from typing import Optional

import strawberry


def test_renaming_input_fields():
    @strawberry.input
    class FilterInput:
        in_: Optional[str] = strawberry.field(name="in", default=strawberry.UNSET)

    @strawberry.type
    class Query:
        hello: str = "Hello"

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def filter(self, input: FilterInput) -> str:
            return f"Hello {input.in_ or 'nope'}"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = "mutation { filter(input: {}) }"

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data
    assert result.data["filter"] == "Hello nope"

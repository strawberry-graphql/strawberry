from typing_extensions import TypedDict

import strawberry


# TODO: do benchmarks for comparison
# TODO: check also __slots__
# TODO: this might still be ok to do since we want to allow people
# to properly type things
def test_basic_typed_dict():
    @strawberry.type
    class User(TypedDict):
        name: str

    # TODO: check that User is not a dataclass :)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return {"name": "Patrick"}

    schema = strawberry.Schema(query=Query)

    query = "{ user { name } }"

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors

    assert result.data
    assert result.data["user"] == {"name": "Patrick"}

"""`strawberry.Maybe` fields of pydantic inputs with postponed annotations."""

from __future__ import annotations

import pydantic
from inline_snapshot import snapshot

import strawberry

# Types are defined at module level: with postponed annotations, pydantic and
# Strawberry resolve the string annotations from the module namespace.


@strawberry.pydantic.input
class AddressInput(pydantic.BaseModel):
    city: str


@strawberry.pydantic.input
class UpdateUserInput(pydantic.BaseModel):
    name: strawberry.Maybe[str]
    address: strawberry.Maybe[AddressInput | None]


@strawberry.type
class Query:
    @strawberry.field
    def update(self, input: UpdateUserInput) -> str:
        return repr(input)


def test_maybe_fields():
    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
input AddressInput {
  city: String!
}

type Query {
  update(input: UpdateUserInput!): String!
}

input UpdateUserInput {
  name: String
  address: AddressInput
}\
""")

    result = schema.execute_sync(
        '{ update(input: { name: "Ada", address: { city: "London" } }) }'
    )

    assert not result.errors
    assert result.data == {
        "update": "UpdateUserInput(name=Some('Ada'), address=Some(AddressInput(city='London')))"
    }

    assert UpdateUserInput().model_fields_set == set()

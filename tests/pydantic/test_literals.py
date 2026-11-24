from typing import Annotated, Literal

import pydantic
import pytest

import strawberry


@pytest.mark.xfail(
    reason=(
        "Literal support is tracked in "
        "https://github.com/strawberry-graphql/strawberry/pull/4522"
    ),
    strict=True,
)
def test_discriminated_union_with_literal_discriminator() -> None:
    @strawberry.pydantic.type
    class Cat(pydantic.BaseModel):
        kind: Literal["cat"]
        lives: int

    @strawberry.pydantic.type
    class Dog(pydantic.BaseModel):
        kind: Literal["dog"]
        bark_volume: int

    Pet = Annotated[Cat | Dog, pydantic.Field(discriminator="kind")]

    @strawberry.pydantic.type
    class Owner(pydantic.BaseModel):
        pet: Pet

    @strawberry.type
    class Query:
        owner: Owner

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        """
        query {
          owner {
            pet {
              ... on Cat { lives }
              ... on Dog { barkVolume }
            }
          }
        }
        """,
        root_value=Query(owner=Owner(pet=Cat(kind="cat", lives=9))),
    )

    assert not result.errors
    assert result.data == {"owner": {"pet": {"lives": 9}}}

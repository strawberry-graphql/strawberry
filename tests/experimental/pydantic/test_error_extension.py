from pydantic import BaseModel, Field

import strawberry
from strawberry.experimental.pydantic import input as pydantic_input
from strawberry.extensions import PydanticErrorExtension


class UserModel(BaseModel):
    age: int = Field(gt=18)
    score: int = Field(gt=50)


@pydantic_input(model=UserModel)
class UserInput:
    age: int
    score: int


@strawberry.type
class Query:
    hello: str = "hi"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, data: UserInput) -> bool:
        UserModel(**data.__dict__)
        return True


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[PydanticErrorExtension],
)


def test_single_validation_error():
    result = schema.execute_sync(
        """
        mutation {
            createUser(data: { age: 10, score: 60 })
        }
        """
    )

    assert result.errors is not None
    extensions = result.errors[0].extensions or {}
    assert "validation_errors" in extensions

    errors = extensions["validation_errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "age"


def test_multiple_validation_errors():
    result = schema.execute_sync(
        """
        mutation {
            createUser(data: { age: 10, score: 40 })
        }
        """
    )

    assert result.errors is not None
    extensions = result.errors[0].extensions or {}
    assert "validation_errors" in extensions

    errors = extensions["validation_errors"]
    fields = [e["field"] for e in errors]

    assert "age" in fields
    assert "score" in fields
    assert len(errors) == 2

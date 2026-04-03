import strawberry
from pydantic import BaseModel, EmailStr
from strawberry.extensions.pydantic_error_extension import PydanticErrorExtension


class UserModel(BaseModel):
    email: EmailStr


@strawberry.type
class Query:
    hello: str = "hi"


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, email: str) -> str:
        UserModel(email=email)
        return "ok"


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[PydanticErrorExtension],
)


def test_pydantic_error_formatting():
    result = schema.execute_sync(
        """
        mutation {
            createUser(email: "not-an-email")
        }
        """
    )

    assert result.errors is not None
    assert "validation_errors" in result.errors[0].extensions
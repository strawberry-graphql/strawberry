from inline_snapshot import snapshot

import pydantic
import strawberry


def test_pydantic_field_aliases_in_execution():
    """Test that Pydantic field aliases work in GraphQL execution."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: str = pydantic.Field(alias="fullName")
        age: int = pydantic.Field(alias="yearsOld")

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            # When using aliases, we need to create the User with the aliased field names
            return User(fullName="John", yearsOld=30)

    schema = strawberry.Schema(query=Query)

    # Query using the aliased field names
    query = """
        query {
            getUser {
                fullName
                yearsOld
            }
        }
    """

    result = schema.execute_sync(query)

    assert not result.errors
    assert result.data == snapshot({"getUser": {"fullName": "John", "yearsOld": 30}})

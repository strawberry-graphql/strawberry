from typing import Annotated

import pydantic

import strawberry


def test_pydantic_field_descriptions_in_schema():
    """Test that Pydantic field descriptions appear in the schema."""

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        name: Annotated[str, pydantic.Field(description="The user's full name")]
        age: Annotated[int, pydantic.Field(description="The user's age in years")]

    @strawberry.type
    class Query:
        @strawberry.field
        def get_user(self) -> User:
            return User(name="John", age=30)

    schema = strawberry.Schema(query=Query)

    # Check that the schema includes field descriptions
    schema_str = str(schema)
    assert "The user's full name" in schema_str
    assert "The user's age in years" in schema_str

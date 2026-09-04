import pytest

import strawberry

pytestmark = pytest.mark.pydantic


def test_use_alias_as_gql_name():
    from pydantic import BaseModel, Field

    class UserModel(BaseModel):
        age_: int = Field(..., alias="age_alias")

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=True
    )
    class User: ...

    @strawberry.type
    class Query:
        user: User = strawberry.field(default_factory=lambda: User(age_=5))

    schema = strawberry.Schema(query=Query)
    query = """{
        user {
            __typename,

            ... on User {
                age_alias
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] == {"__typename": "User", "age_alias": 5}


def test_do_not_use_alias_as_gql_name():
    from pydantic import BaseModel, Field

    class UserModel(BaseModel):
        age_: int = Field(..., alias="age_alias")

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=False
    )
    class User: ...

    @strawberry.type
    class Query:
        user: User = strawberry.field(default_factory=lambda: User(age_=5))

    schema = strawberry.Schema(query=Query)
    query = """{
        user {
            __typename,

            ... on User {
                age_
            }
        }
    }"""

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors
    assert result.data["user"] == {"__typename": "User", "age_": 5}


@pytest.mark.parametrize(
    "use_pydantic_default, expected_raw_interests, expected_pydantic",
    [
        (False, "UNSET", {"name": "John", "interests": []}),
        (True, [], {"name": "John", "interests": []}),
    ],
)
def test_graphql_input_use_pydantic_default_integration(
    use_pydantic_default,
    expected_raw_interests,
    expected_pydantic,
):
    from pydantic import BaseModel, Field

    class UserModel(BaseModel):
        name: str
        interests: list[str] | None = Field(default_factory=list)

    @strawberry.experimental.pydantic.input(
        UserModel,
        use_pydantic_default=use_pydantic_default,
    )
    class UpdateUserInput:
        name: strawberry.auto
        interests: strawberry.auto

    @strawberry.type
    class RawResult:
        name: str
        interests: strawberry.scalars.JSON

    @strawberry.type
    class PydanticResult:
        name: str
        interests: strawberry.scalars.JSON | None

    @strawberry.type
    class UpdateResult:
        raw: RawResult
        pydantic: PydanticResult

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def update_user(self, user_data: UpdateUserInput) -> UpdateResult:
            raw_dict = strawberry.asdict(user_data)
            p_dict = user_data.to_pydantic().model_dump()

            # JSON-friendly representation
            raw_interests = raw_dict["interests"]
            if raw_interests is strawberry.UNSET:
                raw_interests = "UNSET"

            return UpdateResult(
                raw=RawResult(
                    name=raw_dict["name"],
                    interests=raw_interests,
                ),
                pydantic=PydanticResult(
                    name=p_dict["name"],
                    interests=p_dict.get("interests"),
                ),
            )

    @strawberry.type
    class Query:
        ok: bool

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    query = """
        mutation {
            updateUser(userData: { name: "John" }) {
                raw { name interests }
                pydantic { name interests }
            }
        }
    """

    result = schema.execute_sync(query)
    assert not result.errors

    raw = result.data["updateUser"]["raw"]
    pyd = result.data["updateUser"]["pydantic"]

    assert raw["name"] == "John"
    assert raw["interests"] == expected_raw_interests

    assert pyd == expected_pydantic

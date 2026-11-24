from collections.abc import Callable
from typing import Annotated, Any

import pydantic
import pytest
from pydantic import AliasChoices, AliasPath, Field
from pydantic.alias_generators import to_snake

import strawberry


@pytest.mark.parametrize(
    ("config", "field"),
    [
        pytest.param({}, lambda: Field(alias="login"), id="alias"),
        pytest.param({}, lambda: Field(validation_alias="login"), id="validation"),
        pytest.param(
            {},
            lambda: Field(validation_alias=AliasChoices("login", "nick")),
            id="choices",
        ),
        pytest.param(
            {}, lambda: Field(validation_alias=AliasPath("account", "login")), id="path"
        ),
        pytest.param({"alias_generator": str.upper}, Field, id="generator"),
        pytest.param(
            {"populate_by_name": True}, lambda: Field(alias="login"), id="populate"
        ),
    ],
)
def test_inputs_with_aliases_are_validated_by_name(
    config: pydantic.ConfigDict, field: Callable[[], Any]
):
    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        model_config = config

        user_name: str = field()

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: UserInput) -> str:
            return input.user_name

    schema = strawberry.Schema(query=Query)

    assert "input UserInput {\n  userName: String!\n}" in str(schema)

    result = schema.execute_sync('{ user(input: {userName: "Ada"}) }')

    assert not result.errors
    assert result.data == {"user": "Ada"}


def test_strawberry_name_overrides_pydantic_alias():
    """Test that strawberry.field(name=...) overrides Pydantic alias for GraphQL."""

    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        internal_id: Annotated[str, strawberry.field(name="productId")] = Field(
            alias="id"
        )

    @strawberry.pydantic.input
    class ProductInput(pydantic.BaseModel):
        internal_id: Annotated[str, strawberry.field(name="productId")] = Field(
            alias="id"
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self, input: ProductInput) -> Product:
            return Product(id=input.internal_id)

    schema = strawberry.Schema(query=Query)

    assert "type Product {\n  productId: String!\n}" in str(schema)
    assert "input ProductInput {\n  productId: String!\n}" in str(schema)

    result = schema.execute_sync(
        """
        query {
            product(input: { productId: "P123" }) {
                productId
            }
        }
        """
    )

    assert not result.errors
    assert result.data["product"]["productId"] == "P123"


def test_aliases_are_not_used_as_graphql_names():
    @strawberry.pydantic.type
    class ExternalUser(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(alias_generator=to_snake)

        userName: str  # noqa: N815
        created_at: str = Field(alias="created-at")

    @strawberry.pydantic.input
    class ExternalUserInput(pydantic.BaseModel):
        user_name: str = Field(alias="user-name", min_length=2)

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, input: ExternalUserInput) -> ExternalUser:
            return ExternalUser(user_name=input.user_name, **{"created-at": "today"})

    schema = strawberry.Schema(query=Query)

    assert "type ExternalUser {\n  userName: String!\n  createdAt: String!\n}" in str(
        schema
    )
    assert "input ExternalUserInput {\n  userName: String!\n}" in str(schema)

    result = schema.execute_sync(
        '{ user(input: {userName: "Ada"}) { userName createdAt } }'
    )

    assert not result.errors
    assert result.data == {"user": {"userName": "Ada", "createdAt": "today"}}

    result = schema.execute_sync('{ user(input: {userName: "A"}) { userName } }')

    assert result.errors
    assert result.errors[0].extensions["validationErrors"][0]["location"] == [
        "input",
        "userName",
    ]


def test_aliases_matching_other_fields():
    @strawberry.pydantic.input
    class SwapInput(pydantic.BaseModel):
        first: str = Field(alias="second")
        second: str = Field(alias="first")

    @strawberry.type
    class Query:
        @strawberry.field
        def swap(self, input: SwapInput) -> str:
            return f"{input.first} {input.second}"

    result = strawberry.Schema(query=Query).execute_sync(
        '{ swap(input: {first: "F", second: "S"}) }'
    )

    assert not result.errors
    assert result.data == {"swap": "F S"}

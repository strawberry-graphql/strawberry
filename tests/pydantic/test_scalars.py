import io
from typing import Annotated, NewType

import pydantic
import pytest
from inline_snapshot import snapshot

import strawberry
from strawberry.file_uploads import Upload
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig

UserId = NewType("UserId", int)
Money = NewType("Money", str)


def test_id_fields():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: strawberry.ID
        friend_ids: list[strawberry.ID]
        manager_id: strawberry.ID | None = None

    @strawberry.pydantic.input
    class UserFilter(pydantic.BaseModel):
        id: strawberry.ID

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, filter: UserFilter) -> User:
            return User(id=filter.id, friend_ids=[strawberry.ID("2")])

    schema = strawberry.Schema(query=Query)

    assert str(schema) == snapshot("""\
type Query {
  user(filter: UserFilter!): User!
}

type User {
  id: ID!
  friendIds: [ID!]!
  managerId: ID
}

input UserFilter {
  id: ID!
}\
""")

    # ID accepts integer literals, which String doesn't
    result = schema.execute_sync("{ user(filter: {id: 1}) { id friendIds managerId } }")

    assert not result.errors
    assert result.data == {"user": {"id": "1", "friendIds": ["2"], "managerId": None}}


def test_json_fields():
    @strawberry.pydantic.type
    class Settings(pydantic.BaseModel):
        values: JSON

    @strawberry.pydantic.input
    class SettingsInput(pydantic.BaseModel):
        values: JSON

    @strawberry.type
    class Query:
        @strawberry.field
        def settings(self, input: SettingsInput) -> Settings:
            return Settings(values=input.values)

    schema = strawberry.Schema(query=Query)

    assert "values: JSON!" in str(schema)

    result = schema.execute_sync(
        '{ settings(input: {values: {theme: "dark", fontSize: 12}}) { values } }'
    )

    assert not result.errors
    assert result.data == {"settings": {"values": {"theme": "dark", "fontSize": 12}}}


def test_upload_fields_on_inputs():
    # Uploads are the integration's file objects, not `bytes`, so pydantic
    # validates them as the file type while GraphQL uses the Upload scalar
    @strawberry.pydantic.input
    class CreatePostInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

        title: str
        image: Annotated[io.BytesIO, strawberry.field(graphql_type=Upload)]

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_post(self, input: CreatePostInput) -> str:
            return input.image.read().decode()

    @strawberry.type
    class Query:
        hello: str = "world"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    assert "image: Upload!" in str(schema)

    result = schema.execute_sync(
        'mutation ($image: Upload!) { createPost(input: {title: "Hi", image: $image}) }',
        variable_values={"image": io.BytesIO(b"image content")},
    )

    assert not result.errors
    assert result.data == {"createPost": "image content"}


def test_scalar_map_new_types():
    @strawberry.pydantic.type
    class Product(pydantic.BaseModel):
        price: Money

    @strawberry.pydantic.input
    class ProductInput(pydantic.BaseModel):
        price: Money

    @strawberry.type
    class Query:
        @strawberry.field
        def product(self, input: ProductInput) -> Product:
            return Product(price=input.price)

    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                Money: strawberry.scalar(
                    name="Money",
                    serialize=lambda value: f"{value} EUR",
                    parse_value=lambda value: value.removesuffix(" EUR"),
                )
            }
        ),
    )

    assert "price: Money!" in str(schema)

    result = schema.execute_sync(
        "query ($price: Money!) { product(input: {price: $price}) { price } }",
        variable_values={"price": "10 EUR"},
    )

    assert not result.errors
    assert result.data == {"product": {"price": "10 EUR"}}


def test_unregistered_new_types_are_rejected_like_strawberry_types():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: UserId

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    with pytest.raises(
        TypeError,
        match=r"User fields cannot be resolved\. Unexpected type '.*\.UserId'",
    ):
        strawberry.Schema(query=Query)


def test_new_types_can_be_exposed_as_their_base_type():
    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: Annotated[UserId, strawberry.field(graphql_type=int)]

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id=UserId(1))

    schema = strawberry.Schema(query=Query)

    assert "id: Int!" in str(schema)

    result = schema.execute_sync("{ user { id } }")

    assert not result.errors
    assert result.data == {"user": {"id": 1}}

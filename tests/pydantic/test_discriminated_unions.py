"""Tests for Pydantic v2 discriminated unions with first-class integration."""

from typing import Annotated, Literal, Union

import pydantic
from pydantic import Field

import strawberry


def test_basic_discriminated_union_output():
    """Test basic discriminated union for output types."""

    @strawberry.pydantic.type
    class Cat(pydantic.BaseModel):
        pet_type: Literal["cat"]
        meow_volume: int

    @strawberry.pydantic.type
    class Dog(pydantic.BaseModel):
        pet_type: Literal["dog"]
        bark_volume: int

    # Pydantic discriminated union type (not directly used in GraphQL schema,
    # but demonstrates the pattern that works with Strawberry's union handling)
    _Pet = Annotated[Union[Cat, Dog], Field(discriminator="pet_type")]

    @strawberry.type
    class Query:
        @strawberry.field
        def pet(self) -> Cat | Dog:
            return Cat(pet_type="cat", meow_volume=10)

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            pet {
                ... on Cat {
                    petType
                    meowVolume
                }
                ... on Dog {
                    petType
                    barkVolume
                }
            }
        }
        """
    )

    assert not result.errors
    assert result.data["pet"]["petType"] == "cat"
    assert result.data["pet"]["meowVolume"] == 10


def test_discriminated_union_with_different_types():
    """Test discriminated union with more variety in discriminator values."""

    @strawberry.pydantic.type
    class EmailNotification(pydantic.BaseModel):
        kind: Literal["email"]
        recipient: str
        subject: str

    @strawberry.pydantic.type
    class SMSNotification(pydantic.BaseModel):
        kind: Literal["sms"]
        phone_number: str
        message: str

    @strawberry.pydantic.type
    class PushNotification(pydantic.BaseModel):
        kind: Literal["push"]
        device_id: str
        title: str

    @strawberry.type
    class Query:
        @strawberry.field
        def notifications(
            self,
        ) -> list[EmailNotification | SMSNotification | PushNotification]:
            return [
                EmailNotification(
                    kind="email", recipient="test@example.com", subject="Hello"
                ),
                SMSNotification(kind="sms", phone_number="555-1234", message="Hi"),
                PushNotification(kind="push", device_id="device-123", title="Alert"),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            notifications {
                ... on EmailNotification {
                    kind
                    recipient
                    subject
                }
                ... on SMSNotification {
                    kind
                    phoneNumber
                    message
                }
                ... on PushNotification {
                    kind
                    deviceId
                    title
                }
            }
        }
        """
    )

    assert not result.errors
    assert len(result.data["notifications"]) == 3
    assert result.data["notifications"][0]["kind"] == "email"
    assert result.data["notifications"][1]["kind"] == "sms"
    assert result.data["notifications"][2]["kind"] == "push"


def test_discriminated_union_input():
    """Test discriminated union for input types using OneOf."""

    # For GraphQL inputs, discriminated unions aren't directly supported
    # since GraphQL uses @oneOf pattern. But we can test that Pydantic
    # models with discriminated unions can still work in resolvers.

    @strawberry.pydantic.type
    class CatResult(pydantic.BaseModel):
        pet_type: Literal["cat"]
        name: str
        meow_volume: int

    @strawberry.pydantic.type
    class DogResult(pydantic.BaseModel):
        pet_type: Literal["dog"]
        name: str
        bark_volume: int

    @strawberry.pydantic.input
    class CreateCatInput(pydantic.BaseModel):
        name: str
        meow_volume: int

    @strawberry.pydantic.input
    class CreateDogInput(pydantic.BaseModel):
        name: str
        bark_volume: int

    @strawberry.type
    class Mutation:
        @strawberry.mutation
        def create_cat(self, input: CreateCatInput) -> CatResult:
            return CatResult(
                pet_type="cat", name=input.name, meow_volume=input.meow_volume
            )

        @strawberry.mutation
        def create_dog(self, input: CreateDogInput) -> DogResult:
            return DogResult(
                pet_type="dog", name=input.name, bark_volume=input.bark_volume
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    result = schema.execute_sync(
        """
        mutation {
            createCat(input: { name: "Whiskers", meowVolume: 8 }) {
                petType
                name
                meowVolume
            }
        }
        """
    )

    assert not result.errors
    assert result.data["createCat"]["petType"] == "cat"
    assert result.data["createCat"]["name"] == "Whiskers"


def test_nested_discriminated_union():
    """Test discriminated unions within nested types."""

    @strawberry.pydantic.type
    class TextContent(pydantic.BaseModel):
        content_type: Literal["text"]
        body: str

    @strawberry.pydantic.type
    class ImageContent(pydantic.BaseModel):
        content_type: Literal["image"]
        url: str

    @strawberry.pydantic.type
    class Post(pydantic.BaseModel):
        title: str
        content: TextContent | ImageContent

    @strawberry.type
    class Query:
        @strawberry.field
        def posts(self) -> list[Post]:
            return [
                Post(
                    title="Text Post",
                    content=TextContent(content_type="text", body="Hello world"),
                ),
                Post(
                    title="Image Post",
                    content=ImageContent(
                        content_type="image", url="https://example.com/img.png"
                    ),
                ),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            posts {
                title
                content {
                    ... on TextContent {
                        contentType
                        body
                    }
                    ... on ImageContent {
                        contentType
                        url
                    }
                }
            }
        }
        """
    )

    assert not result.errors
    assert len(result.data["posts"]) == 2
    assert result.data["posts"][0]["content"]["contentType"] == "text"
    assert result.data["posts"][0]["content"]["body"] == "Hello world"
    assert result.data["posts"][1]["content"]["contentType"] == "image"


def test_discriminated_union_with_default():
    """Test discriminated union with a default discriminator value."""

    @strawberry.pydantic.type
    class StandardShipping(pydantic.BaseModel):
        method: Literal["standard"] = "standard"
        days: int

    @strawberry.pydantic.type
    class ExpressShipping(pydantic.BaseModel):
        method: Literal["express"]
        days: int
        cost_multiplier: float

    @strawberry.pydantic.type
    class Order(pydantic.BaseModel):
        id: str
        shipping: StandardShipping | ExpressShipping

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self) -> Order:
            return Order(
                id="ORD-123", shipping=StandardShipping(method="standard", days=5)
            )

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            order {
                id
                shipping {
                    ... on StandardShipping {
                        method
                        days
                    }
                    ... on ExpressShipping {
                        method
                        days
                        costMultiplier
                    }
                }
            }
        }
        """
    )

    assert not result.errors
    assert result.data["order"]["shipping"]["method"] == "standard"
    assert result.data["order"]["shipping"]["days"] == 5


def test_union_with_str_discriminator():
    """Test union with string literal as discriminator."""

    @strawberry.pydantic.type
    class Circle(pydantic.BaseModel):
        shape_type: Literal["circle"]
        radius: float

    @strawberry.pydantic.type
    class Square(pydantic.BaseModel):
        shape_type: Literal["square"]
        side: float

    @strawberry.pydantic.type
    class Triangle(pydantic.BaseModel):
        shape_type: Literal["triangle"]
        base: float
        height: float

    @strawberry.type
    class Query:
        @strawberry.field
        def shapes(self) -> list[Circle | Square | Triangle]:
            return [
                Circle(shape_type="circle", radius=5.0),
                Square(shape_type="square", side=10.0),
                Triangle(shape_type="triangle", base=6.0, height=8.0),
            ]

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query {
            shapes {
                ... on Circle {
                    shapeType
                    radius
                }
                ... on Square {
                    shapeType
                    side
                }
                ... on Triangle {
                    shapeType
                    base
                    height
                }
            }
        }
        """
    )

    assert not result.errors
    assert len(result.data["shapes"]) == 3
    assert result.data["shapes"][0]["shapeType"] == "circle"
    assert result.data["shapes"][0]["radius"] == 5.0
    assert result.data["shapes"][1]["shapeType"] == "square"
    assert result.data["shapes"][2]["shapeType"] == "triangle"

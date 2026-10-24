from enum import Enum

import pydantic
from inline_snapshot import snapshot
from pytest_mock import MockerFixture

import strawberry
from strawberry import relay
from strawberry.types.arguments import InputContext
from strawberry.types.base import get_object_definition


def test_basic_input_type():
    """Test that @strawberry.pydantic.input works."""

    @strawberry.pydantic.input
    class CreateUserInput(pydantic.BaseModel):
        age: int
        name: str

    definition = get_object_definition(CreateUserInput, strict=True)

    assert definition.name == "CreateUserInput"
    assert definition.is_input is True
    assert len(definition.fields) == 2


def test_input_type_with_valid_data():
    """Test input type with various valid data scenarios."""

    @strawberry.pydantic.input
    class UserInput(pydantic.BaseModel):
        name: str
        age: int
        email: str
        is_active: bool = True
        tags: list[str] = []

    @strawberry.pydantic.type
    class User(pydantic.BaseModel):
        id: int
        name: str
        age: int
        email: str
        is_active: bool
        tags: list[str]

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_user(self, input: UserInput) -> User:
            return User(
                id=1,
                name=input.name,
                age=input.age,
                email=input.email,
                is_active=input.is_active,
                tags=input.tags,
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def dummy(self) -> str:
            return "dummy"

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    # Test with all fields provided
    mutation = """
        mutation {
            createUser(input: {
                name: "John Doe"
                age: 30
                email: "john@example.com"
                isActive: false
                tags: ["developer", "python"]
            }) {
                id
                name
                age
                email
                isActive
                tags
            }
        }
    """

    result = schema.execute_sync(mutation)

    assert not result.errors
    assert result.data == snapshot(
        {
            "createUser": {
                "id": 1,
                "name": "John Doe",
                "age": 30,
                "email": "john@example.com",
                "isActive": False,
                "tags": ["developer", "python"],
            }
        }
    )

    # Test with default values
    mutation_defaults = """
        mutation {
            createUser(input: {
                name: "Jane Doe"
                age: 25
                email: "jane@example.com"
            }) {
                id
                name
                age
                email
                isActive
                tags
            }
        }
    """

    result = schema.execute_sync(mutation_defaults)

    assert not result.errors
    assert result.data == snapshot(
        {
            "createUser": {
                "id": 1,
                "name": "Jane Doe",
                "age": 25,
                "email": "jane@example.com",
                "isActive": True,  # default value
                "tags": [],  # default value
            }
        }
    )


def test_one_of_inputs():
    @strawberry.pydantic.input(one_of=True)
    class UserBy(pydantic.BaseModel):
        id: strawberry.ID | None = None
        email: str | None = None

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self, by: UserBy) -> str:
            return repr(by.model_dump(exclude_unset=True))

    schema = strawberry.Schema(query=Query)

    assert "input UserBy @oneOf {\n  id: ID\n  email: String\n}" in str(schema)

    result = schema.execute_sync('{ user(by: {email: "ada@example.com"}) }')

    assert not result.errors
    assert result.data == {"user": "{'email': 'ada@example.com'}"}

    result = schema.execute_sync('{ user(by: {id: "1", email: "ada@example.com"}) }')

    assert result.errors


def test_list_items_are_converted_like_in_strawberry_inputs():
    @strawberry.enum
    class Color(Enum):
        RED = "red"
        BLUE = "blue"

    @strawberry.input
    class TagInput:
        name: str

    @strawberry.pydantic.input
    class FilterInput(pydantic.BaseModel):
        colors: list[Color]
        ids: list[relay.GlobalID]
        scores: list[float | None]
        grid: list[list[int]]
        tags: list[TagInput]

    received: list[FilterInput] = []

    @strawberry.type
    class Query:
        @strawberry.field
        def search(self, filter: FilterInput) -> bool:
            received.append(filter)

            return True

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        query ($filter: FilterInput!) {
            search(filter: $filter)
        }
        """,
        variable_values={
            "filter": {
                "colors": ["RED", "BLUE"],
                "ids": [str(relay.GlobalID("Fruit", "1"))],
                "scores": [0.5, None],
                "grid": [[1, 2], [], [3]],
                "tags": [{"name": "jam"}],
            }
        },
    )

    assert not result.errors
    assert received == [
        FilterInput(
            colors=[Color.RED, Color.BLUE],
            ids=[relay.GlobalID("Fruit", "1")],
            scores=[0.5, None],
            grid=[[1, 2], [], [3]],
            tags=[TagInput(name="jam")],
        )
    ]


def test_only_lists_of_nested_models_are_converted_item_by_item(
    mocker: MockerFixture,
):
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        quantity: int

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        ids: list[int]
        items: list[ItemInput]

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> bool:
            return True

    schema = strawberry.Schema(query=Query)
    convert = mocker.spy(InputContext, "convert")

    result = schema.execute_sync(
        "{ order(input: {ids: [1, 2, 3], items: [{quantity: 1}, {quantity: 2}]}) }"
    )

    assert not result.errors
    # other lists are converted with a single call, which is a lot faster for
    # long lists of scalars
    assert [call.args[3:] for call in convert.call_args_list] == [
        ("ids",),
        ("items", 0, "quantity"),
        ("items", 1, "quantity"),
    ]


def test_tuple_fields_get_tuples():
    # in strict mode, pydantic doesn't accept the lists of GraphQL for tuples
    @strawberry.pydantic.input
    class ItemInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)

        quantity: int

    @strawberry.pydantic.input
    class OrderInput(pydantic.BaseModel):
        model_config = pydantic.ConfigDict(strict=True)

        labels: tuple[str, ...]
        size: tuple[int, int] | None
        grid: list[tuple[int, ...]]
        items: tuple[ItemInput, ...]

    received: list[OrderInput] = []

    @strawberry.type
    class Query:
        @strawberry.field
        def order(self, input: OrderInput) -> bool:
            received.append(input)

            return True

    schema = strawberry.Schema(query=Query)

    result = schema.execute_sync(
        """
        {
            order(input: {
                labels: ["sale"]
                size: [2, 3]
                grid: [[1, 2], []]
                items: [{quantity: 1}]
            })
        }
        """
    )

    assert not result.errors
    assert received == [
        OrderInput(
            labels=("sale",),
            size=(2, 3),
            grid=[(1, 2), ()],
            items=(ItemInput(quantity=1),),
        )
    ]

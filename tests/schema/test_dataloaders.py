import asyncio
from dataclasses import dataclass

import pytest

import strawberry
from strawberry.dataloader import DataLoader


@pytest.mark.asyncio
async def test_can_use_dataloaders(mocker):
    @dataclass
    class User:
        id: str

    async def idx(keys) -> list[User]:
        return [User(key) for key in keys]

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader)

    @strawberry.type
    class Query:
        @strawberry.field
        async def get_user(self, id: strawberry.ID) -> str:
            user = await loader.load(id)

            return user.id

    schema = strawberry.Schema(query=Query)

    query = """{
        a: getUser(id: "1")
        b: getUser(id: "2")
    }"""

    result = await schema.execute(query)

    assert not result.errors
    assert result.data == {
        "a": "1",
        "b": "2",
    }

    mock_loader.assert_called_once_with(["1", "2"])


@pytest.mark.asyncio
async def test_failing_field_does_not_cancel_dataloader_of_other_fields():
    """graphql-core cancels the sibling resolvers of a failing non-null field.
    A sibling waiting on a key shared with another, healthy, field must not
    break that field.
    """

    async def load_names(keys: list[int]) -> list[str]:
        await asyncio.sleep(0.01)
        return [f"name-{key}" for key in keys]

    @strawberry.type
    class Item:
        loader: strawberry.Private[DataLoader[int, str]]

        @strawberry.field
        async def name(self) -> str:
            return await self.loader.load(1)

        @strawberry.field
        async def failing_field(self) -> str:
            await asyncio.sleep(0)
            raise ValueError("Failing field")

    @strawberry.type
    class Query:
        loader: strawberry.Private[DataLoader[int, str]]

        @strawberry.field
        def item(self) -> Item | None:
            return Item(loader=self.loader)

        @strawberry.field
        def failing_item(self) -> Item | None:
            return Item(loader=self.loader)

    schema = strawberry.Schema(query=Query)

    result = await schema.execute(
        "{ item { name } failingItem { name failingField } }",
        root_value=Query(loader=DataLoader(load_fn=load_names)),
    )

    assert result.data == {"item": {"name": "name-1"}, "failingItem": None}
    assert result.errors is not None
    assert [error.message for error in result.errors] == ["Failing field"]

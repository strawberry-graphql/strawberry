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

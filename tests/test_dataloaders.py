import asyncio

import pytest

from strawberry.dataloader import DataLoader


pytestmark = pytest.mark.asyncio


async def test_loading():
    async def idx(keys):
        return keys

    loader = DataLoader(load_fn=idx)

    value_a = await loader.load(1)
    value_b = await loader.load(2)
    value_c = await loader.load(3)

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3


async def test_gathering(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader)

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )

    mock_loader.assert_called_once_with([1, 2, 3])

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3


async def test_max_batch_size(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader, max_batch_size=2)

    [value_a, value_b, value_c] = await asyncio.gather(
        loader.load(1),
        loader.load(2),
        loader.load(3),
    )

    mock_loader.assert_has_calls([mocker.call([1, 2]), mocker.call([3])])

    assert value_a == 1
    assert value_b == 2
    assert value_c == 3


async def test_error():
    async def idx(keys):
        return [ValueError()]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)


async def test_error_and_values():
    async def idx(keys):
        if keys == [2]:
            return [2]

        return [ValueError()]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)

    assert await loader.load(2) == 2

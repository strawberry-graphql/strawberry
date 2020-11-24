import asyncio

import pytest

from strawberry.dataloader import DataLoader
from strawberry.exceptions import WrongNumberOfResultsReturned


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


async def test_when_raising_error_in_loader():
    async def idx(keys):
        raise ValueError()

    loader = DataLoader(load_fn=idx)

    with pytest.raises(ValueError):
        await loader.load(1)

    with pytest.raises(ValueError):
        await asyncio.gather(
            loader.load(1),
            loader.load(2),
            loader.load(3),
        )


async def test_returning_wrong_number_of_results():
    async def idx(keys):
        return [1, 2]

    loader = DataLoader(load_fn=idx)

    with pytest.raises(
        WrongNumberOfResultsReturned,
        match=(
            "Received wrong number of results in dataloader, "
            "expected: 1, received: 2"
        ),
    ):
        await loader.load(1)


async def test_caches_by_id(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader, cache=True)

    a = loader.load(1)
    b = loader.load(1)

    assert a == b

    assert await a == 1
    assert await b == 1

    mock_loader.assert_called_once_with([1])


async def test_caches_by_id_when_loading_many(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader, cache=True)

    a = loader.load(1)
    b = loader.load(1)

    assert a == b

    assert [1, 1] == await asyncio.gather(a, b)

    mock_loader.assert_called_once_with([1])


async def test_cache_disabled(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader, cache=False)

    a = loader.load(1)
    b = loader.load(1)

    assert a != b

    assert await a == 1
    assert await b == 1

    mock_loader.assert_has_calls([mocker.call([1, 1])])


async def test_cache_disabled_immediate_await(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)

    loader = DataLoader(load_fn=mock_loader, cache=False)

    a = await loader.load(1)
    b = await loader.load(1)

    assert a == b

    mock_loader.assert_has_calls([mocker.call([1]), mocker.call([1])])

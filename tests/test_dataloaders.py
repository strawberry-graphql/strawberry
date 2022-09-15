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

    values = await loader.load_many([1, 2, 3, 4, 5, 6])

    assert values == [1, 2, 3, 4, 5, 6]


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


def test_works_when_created_in_a_different_loop(mocker):
    async def idx(keys):
        return keys

    mock_loader = mocker.Mock(side_effect=idx)
    loader = DataLoader(load_fn=mock_loader, cache=False)

    loop = asyncio.new_event_loop()

    async def run():
        return await loader.load(1)

    data = loop.run_until_complete(run())

    assert data == 1

    mock_loader.assert_called_once_with([1])


async def test_prime():
    async def idx(keys):
        assert keys, "At least one key must be specified"
        return keys

    loader = DataLoader(load_fn=idx)

    # Basic behavior intact
    a1 = loader.load(1)
    assert await a1 == 1

    # Prime doesn't overrides value
    loader.prime(1, 1.1)
    loader.prime(2, 2.1)
    b1 = loader.load(1)
    b2 = loader.load(2)
    assert await b1 == 1
    assert await b2 == 2.1

    # Unless you tell it to
    loader.prime(1, 1.2, force=True)
    loader.prime(2, 2.2, force=True)
    b1 = loader.load(1)
    b2 = loader.load(2)
    assert await b1 == 1.2
    assert await b2 == 2.2

    # Preset will override pending values, but not cached values
    c2 = loader.load(2)  # This is in cache
    c3 = loader.load(3)  # This is pending
    loader.prime_many({2: 2.3, 3: 3.3}, force=True)
    assert await c2 == 2.2
    assert await c3 == 3.3

    # If we prime all keys in a batch, the load_fn is never called
    # (See assertion in idx)
    c4 = loader.load(4)
    loader.prime_many({4: 4.4})
    await c4 == 4.4

    # Yield to ensure the last batch has been dispatched,
    # despite all values being primed
    await asyncio.sleep(0)


async def test_prime_nocache():
    async def idx(keys):
        assert keys, "At least one key must be specified"
        return keys

    loader = DataLoader(load_fn=idx, cache=False)

    # Primed value is ignored
    loader.prime(1, 1.1)
    a1 = loader.load(1)
    assert await a1 == 1

    # Unless it affects pending value in the current batch
    b1 = loader.load(2)
    loader.prime(2, 2.2)
    assert await b1 == 2.2

    # Yield to ensure the last batch has been dispatched,
    # despite all values being primed
    await asyncio.sleep(0)


async def test_clear():
    batch_num = 0

    async def idx(keys):
        """Maps key => (key, batch_num)"""
        nonlocal batch_num
        batch_num += 1
        return [(key, batch_num) for key in keys]

    loader = DataLoader(load_fn=idx)

    assert await loader.load_many([1, 2, 3]) == [(1, 1), (2, 1), (3, 1)]

    loader.clear(1)

    assert await loader.load_many([1, 2, 3]) == [(1, 2), (2, 1), (3, 1)]

    loader.clear_many([1, 2])

    assert await loader.load_many([1, 2, 3]) == [(1, 3), (2, 3), (3, 1)]

    loader.clear_all()

    assert await loader.load_many([1, 2, 3]) == [(1, 4), (2, 4), (3, 4)]


async def test_clear_nocache():
    batch_num = 0

    async def idx(keys):
        """Maps key => (key, batch_num)"""
        nonlocal batch_num
        batch_num += 1
        return [(key, batch_num) for key in keys]

    loader = DataLoader(load_fn=idx, cache=False)

    assert await loader.load_many([1, 2, 3]) == [(1, 1), (2, 1), (3, 1)]

    loader.clear(1)

    assert await loader.load_many([1, 2, 3]) == [(1, 2), (2, 2), (3, 2)]

    loader.clear_many([1, 2])

    assert await loader.load_many([1, 2, 3]) == [(1, 3), (2, 3), (3, 3)]

    loader.clear_all()

    assert await loader.load_many([1, 2, 3]) == [(1, 4), (2, 4), (3, 4)]

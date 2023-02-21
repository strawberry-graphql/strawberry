from strawberry.utils.aio import (
    aenumerate,
    aislice,
    asyncgen_to_list,
    resolve_awaitable,
)


async def test_aenumerate():
    async def gen():
        yield "a"
        yield "b"
        yield "c"
        yield "d"

    res = [(i, v) async for i, v in aenumerate(gen())]
    assert res == [(0, "a"), (1, "b"), (2, "c"), (3, "d")]


async def test_aslice():
    async def gen():
        yield "a"
        yield "b"
        raise AssertionError("should never be called")  # pragma: no cover
        yield "c"  # pragma: no cover

    res = []
    async for v in aislice(gen(), 0, 2):
        res.append(v)

    assert res == ["a", "b"]


async def test_aslice_with_step():
    async def gen():
        yield "a"
        yield "b"
        yield "c"
        raise AssertionError("should never be called")  # pragma: no cover
        yield "d"  # pragma: no cover
        yield "e"  # pragma: no cover

    res = []
    async for v in aislice(gen(), 0, 4, 2):
        res.append(v)

    assert res == ["a", "c"]


async def test_asyncgen_to_list():
    async def gen():
        yield "a"
        yield "b"
        yield "c"

    assert await asyncgen_to_list(gen()) == ["a", "b", "c"]


async def test_resolve_awaitable():
    async def awaitable():
        return 1

    assert await resolve_awaitable(awaitable(), lambda v: v + 1) == 2

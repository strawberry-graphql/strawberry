from strawberry.utils.inspect import in_async_context


def test_in_async_context_sync():
    assert not in_async_context()


async def test_in_async_context_async():
    assert in_async_context()


async def test_in_async_context_async_with_inner_sync_function():
    def inner_sync_function():
        assert in_async_context()

    inner_sync_function()

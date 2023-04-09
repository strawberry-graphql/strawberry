from typing import Dict


def get_context(context: object) -> Dict[str, object]:
    return get_context_inner(context)


# a patchable method for unittests
def get_context_inner(context: object) -> Dict[str, object]:
    assert isinstance(context, dict)
    return {**context, "custom_value": "a value from context"}


# async version for async frameworks
async def get_context_async(context: object) -> Dict[str, object]:
    return await get_context_async_inner(context)


# a patchable method for unittests
async def get_context_async_inner(context: object) -> Dict[str, object]:
    assert isinstance(context, dict)
    return {**context, "custom_value": "a value from context"}

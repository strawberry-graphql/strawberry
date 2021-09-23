from typing import Tuple, Type

import strawberry


def merge_types(types: Tuple[Type]) -> Type:
    """Merge multiple Strawberry types into one

    For example, given two queries `A` and `B`, one can merge them as follows:

        merge_types((B, A))

    This is essentially the same as:

        class Query(B, A):
            ...
    """

    if not types:
        raise ValueError("Can't merge types if none are supplied")

    return strawberry.type(type("MegaType", types, {}))

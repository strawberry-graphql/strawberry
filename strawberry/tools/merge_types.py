from typing import Tuple, Type

import strawberry


DEFAULT_NAME = "MegaType"


def merge_types(types: Tuple[Type], name: str = DEFAULT_NAME) -> Type:
    """Merge multiple Strawberry types into one

    For example, given two queries `A` and `B`, one can merge them as follows:

        merge_types((B, A))

    This is essentially the same as:

        class Query(B, A):
            ...

    An optional name may be specified for the resulting type.
    """

    if not types:
        raise ValueError("Can't merge types if none are supplied")

    return strawberry.type(type(name, types, {}))

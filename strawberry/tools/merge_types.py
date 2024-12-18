import warnings
from collections import Counter
from itertools import chain

import strawberry
from strawberry.types.base import has_object_definition


def merge_types(name: str, types: tuple[type, ...]) -> type:
    """Merge multiple Strawberry types into one.

    For example, given two queries `A` and `B`, one can merge them into a
    super type as follows:

        merge_types("SuperQuery", (B, A))

    This is essentially the same as:

        class SuperQuery(B, A):
            ...
    """
    if not types:
        raise ValueError("Can't merge types if none are supplied")

    fields = chain(
        *(t.__strawberry_definition__.fields for t in types if has_object_definition(t))
    )
    counter = Counter(f.name for f in fields)
    dupes = [f for f, c in counter.most_common() if c > 1]
    if dupes:
        warnings.warn(
            "{} has overridden fields: {}".format(name, ", ".join(dupes)), stacklevel=2
        )

    return strawberry.type(type(name, types, {}))


__all__ = ["merge_types"]

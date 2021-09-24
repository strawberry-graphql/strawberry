from collections import Counter
from itertools import chain
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

    fields = chain(*(t._type_definition.fields for t in types))
    counter = Counter(f.name for f in fields)
    dupes = [f for f, c in counter.most_common() if c > 1]
    if dupes:
        raise Warning("{} has overridden fields: {}".format(name, ", ".join(dupes)))

    return strawberry.type(type(name, types, {}))

from typing import List

import strawberry


# This is used in the `test_resolver` unit tests for resolvers
# defined in a different module than the dataclass that uses it.
def any_list_resolver():
    return []


def bar_list_resolver() -> List["Bar"]:
    return []


@strawberry.type
class Bar:
    name: str

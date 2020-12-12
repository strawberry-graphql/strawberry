from abc import ABC

from strawberry.types import StrawberryType


class StrawberryInterface(StrawberryType, ABC):
    ...


# TODO
def interface() -> StrawberryInterface:
    ...

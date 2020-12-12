from typing import List, Optional, Union

from strawberry.types import StrawberryObjectType, StrawberryUnion

_OBJECT_FED_TYPE = Union[StrawberryObjectType, 'StrawberryObjectTypeFederation']


# TODO: Should federation use composition or inheritance?
#       i.e. should StrawberryObjectTypeFederation inherit from
#       StrawberryObjectType or just hold a reference to one?

# TODO: This name is probably too long and too verbose. Think of something
class StrawberryObjectTypeFederation:
    """

    TODO: One decorator for federation? Or multiple? This feels a bit stacked
    >>> @strawberry.key("upc")
    ... @strawberry.extends(OtherType)
    ... @strawberry.type
    ... class ThisType:
    ...     @strawberry.field
    ...     def resolver(self) -> OtherType:

    TODO: This is probably better?
    >>> @strawberry.federation(extends=OtherType, key="upc")
    ... @strawberry.type
    ... class ThisType:
    ...     @strawberry.field
    ...     def resolver(self) -> OtherType:

    # TODO: Maybe even this?
    >>> @strawberry.type(extends=OtherType, key="upc")
    ... class ThisType:
    ...     @strawberry.field
    ...     def resolver(self) -> OtherType:

    """

    def __init__(self, cls: _OBJECT_FED_TYPE):

        if isinstance(cls, StrawberryObjectType):
            ...
        elif isinstance(cls, StrawberryObjectTypeFederation):
            ...

    @property
    def entities(self) -> StrawberryUnion:
        ...

    @property
    def extends(self) -> Optional[StrawberryObjectType]:
        ...


class StrawberryFederationKey:

    def __init__(self, keys: List[str]):
        self.keys = keys

    def __call__(self, cls: _OBJECT_FED_TYPE) -> StrawberryObjectTypeFederation:
        if isinstance(cls, StrawberryObjectType):
            ...
        elif isinstance(cls, StrawberryObjectTypeFederation):
            ...

        return ...


def extends(cls: _OBJECT_FED_TYPE) -> StrawberryObjectTypeFederation:
    if isinstance(cls, StrawberryObjectType):
        ...
    elif isinstance(cls, StrawberryObjectTypeFederation):
        ...

    return ...


def key(keys: List[str]) -> StrawberryFederationKey:
    return StrawberryFederationKey(keys)

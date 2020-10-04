from typing import Callable, List, Optional, Type

from strawberry.types import StrawberryArgument, StrawberryObject, \
    StrawberryResolver, StrawberryType


class StrawberryField(StrawberryType):
    """Strawberry field

    >>> StrawberryField(
    ...     type_=int,
    ...     resolver=StrawberryResolver(lambda: 5),
    ...     name="cool_field"
    ... )
    """

    class _NO_DEFAULT_VALUE:
        """Sentinel value to indicate that a field has no default.

        `None` is not a good option because it can actually be the default for a
        nullable type.
        """

    class _NO_FIELD_TYPE:
        """Sentinel value to indicate a field has not received a type"""

    def __init__(
        self, *,
        type_: Optional[Type[StrawberryObject]] = None,
        resolver: Optional[StrawberryResolver] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permission_classes: Optional[object] = None,
    ):
        if (type_ and resolver) and (type_ != resolver.type):
            # TODO: Raise Strawberry exception
            ...

        self._type = type_
        self.resolver = resolver
        self._name = name
        self._description = description
        # TODO: Deal with permissions
        self.permission_classes = permission_classes
        self.default_value: StrawberryObject = self._NO_DEFAULT_VALUE

    def __call__(self, resolver: Callable):
        self.resolver = resolver

    @property
    def arguments(self) -> List[StrawberryArgument]:
        if self.resolver is not None:
            return self.resolver.arguments

        # TODO: Should we raise an exception instead?
        return None

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name

        if self.resolver is not None:
            return self.resolver.__name__

        # TODO: Should we raise an exception instead?
        return None

    @name.setter
    def name(self, name: str):
        self._name = name

    # TODO: Implement
    @property
    def origin(self):
        ...

    @property
    def type(self) -> StrawberryObject:
        # TODO: This can't be set anywhere
        if self._type is not None:
            return self._type

        if self.resolver is not None:
            return self.resolver.type

        # TODO: Should we raise an exception instead?
        return None


def field(
    resolver: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[object] = None,  # TODO
) -> StrawberryField:
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self, info) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    return StrawberryField(
        resolver=resolver,
        name=name,
        description=description,
        permission_classes=permission_classes,
    )

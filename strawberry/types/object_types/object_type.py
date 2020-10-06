import dataclasses
import typing
from typing import Dict, Generic, List, Optional, Protocol, Set, Tuple, Type, \
    TypeVar

from cached_property import cached_property

from strawberry.exceptions import MissingFieldAnnotationError
from strawberry.types import StrawberryField, StrawberryInterface, \
    StrawberryObject
from strawberry.utils.str_converters import to_camel_case

T = TypeVar("T")


class StrawberryObjectType(StrawberryObject, Generic[T]):
    """Base GraphQL object Type

    >>> class SomeType:
    ...     field_a: int
    >>> CoolType = StrawberryObjectType(SomeType)
    >>> CoolerType = StrawberryObjectType(SomeType, name="CoolestType")
    """

    def __init__(
        self,
        cls: '_DataclassType[T]', *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.wrapped_class = cls
        self._name = name
        self._description = description

    def __call__(self, cls: '_DataclassType[T]') -> None:
        self.wrapped_class = cls

    @property
    def description(self) -> Optional[str]:
        return self._description

    @cached_property
    def fields(self) -> Set[StrawberryField]:
        """All the fields on the Type, cached"""

        # TODO: Filter and remove/shadow duplicates that are in both sub and
        #       base
        # TODO: Don't cache somehow if wrapped_class is not set? Throw exc?

        inherited_fields = self._fields_base
        dataclass_fields = self._fields_dataclass
        strawberry_fields = self._fields_strawberry

        fields = inherited_fields | dataclass_fields | strawberry_fields

        return fields

    @cached_property
    def interfaces(self) -> List[StrawberryInterface]:
        interfaces: List[StrawberryInterface] = []
        for base in self.wrapped_class.__bases__:
            if issubclass(base, StrawberryInterface):
                base = typing.cast(StrawberryInterface, base)
                interfaces.append(base)

        return interfaces

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name

        if self.wrapped_class:
            return to_camel_case(self.wrapped_class.__name__)

        # TODO: Should we raise an exception instead?
        return None

    @staticmethod
    def _check_field_annotations(cls: Type[T]):
        """Are any of the dataclass Fields missing type annotations?

        This replicates the check that dataclasses do during creation, but
        allows a proper Strawberry exception to be raised

        https://github.com/python/cpython/blob/6fed3c8/Lib/dataclasses.py#L881-L884
        """
        cls_annotations = cls.__dict__.get("__annotations__", {})

        for field_name, value in cls.__dict__.items():
            if not isinstance(value, dataclasses.Field):
                # Not a dataclasses.Field. Ignore
                continue

            if field_name not in cls_annotations:
                # Field object exists but did not get an annotation
                raise MissingFieldAnnotationError(field_name)

    @cached_property
    def _fields_base(self) -> Set[StrawberryField]:
        """StrawberryFields defined in the base class"""
        inherited_fields: Set[StrawberryField] = set()

        for base in self.wrapped_class.__bases__:
            if issubclass(StrawberryObjectType, base):
                base = typing.cast(StrawberryObjectType, base)
                inherited_fields.update(base.fields)

        return inherited_fields

    @cached_property
    def _fields_dataclass(self) -> Set[StrawberryField]:
        """Fields defined using dataclass-style syntax"""

        dataclass_fields: Set[StrawberryField] = set()
        for field in dataclasses.fields(self.wrapped_class):
            field = typing.cast(dataclasses.Field, field)

            strawberry_field = StrawberryField(
                type_=field.type,
                name=field.name
            )

            dataclass_fields.add(strawberry_field)

        return dataclass_fields

    @cached_property
    def _fields_strawberry(self) -> Set[StrawberryField]:
        """Fields defined using StrawberryField/strawberry.field"""

        # Get fields defined using strawberry.field
        strawberry_fields: Set[StrawberryField] = set()
        for field in self.__dict__.values():
            if isinstance(field, StrawberryField):
                strawberry_fields.add(field)

        return strawberry_fields

    @classmethod
    def check_dataclass(cls, klass: '_DataclassType[T]') -> None:
        """
        TODO: This desc. is wrong
        Wrap a strawberry.type class with a dataclass and check for any
        issues before doing so

        Raises exceptions along the way
        """

        # Ensure all Fields have been properly type-annotated
        # TODO: This is expected to be run _before_ the wrapped class is turned
        #       into a dataclass
        cls._check_field_annotations(klass)


def type(
    cls: Type[T] = None, *, name: str = None, description: str = None,
) -> StrawberryObjectType[T]:
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """
    StrawberryObjectType.check_dataclass(cls)
    wrapped_dataclass = dataclasses.dataclass(cls)

    return StrawberryObjectType(
        cls=wrapped_dataclass,
        name=name,
        description=description
    )


# TODO: Move to another file? Not 100% related to StrawberryObjectType
class _DataclassType(Protocol[T]):
    __dataclass_fields__: Dict
    __bases__: Tuple[Type]

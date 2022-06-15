import sys
import typing
from collections import abc
from enum import Enum
from typing import (  # type: ignore[attr-defined]
    TYPE_CHECKING,
    Any,
    Dict,
    Optional,
    TypeVar,
    Union,
    _eval_type,
)


try:
    from typing import ForwardRef
except ImportError:  # pragma: no cover
    # ForwardRef is private in python 3.6 and 3.7
    from typing import _ForwardRef as ForwardRef  # type: ignore

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.type import (
    StrawberryList,
    StrawberryOptional,
    StrawberryType,
    StrawberryTypeVar,
)
from strawberry.types.types import TypeDefinition
from strawberry.unset import UNSET
from strawberry.utils.typing import is_generic, is_type_var


if TYPE_CHECKING:
    from strawberry.union import StrawberryUnion


ASYNC_TYPES = (
    abc.AsyncGenerator,
    abc.AsyncIterable,
    abc.AsyncIterator,
    typing.AsyncContextManager,
    typing.AsyncGenerator,
    typing.AsyncIterable,
    typing.AsyncIterator,
)


class StrawberryAnnotation:
    def __init__(
        self, annotation: Union[object, str], *, namespace: Optional[Dict] = None
    ):
        self.annotation = annotation
        self.namespace = namespace

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StrawberryAnnotation):
            return NotImplemented

        return self.resolve() == other.resolve()

    def resolve(self) -> Union[StrawberryType, type]:
        annotation: object
        if isinstance(self.annotation, str):
            annotation = ForwardRef(self.annotation)
        else:
            annotation = self.annotation

        evaled_type = _eval_type(annotation, self.namespace, None)
        if self._is_async_type(evaled_type):
            evaled_type = self._strip_async_type(evaled_type)
        if self._is_lazy_type(evaled_type):
            return evaled_type

        if self._is_generic(evaled_type):
            if any(is_type_var(type_) for type_ in evaled_type.__args__):
                return evaled_type
            return self.create_concrete_type(evaled_type)

        # Simply return objects that are already StrawberryTypes
        if self._is_strawberry_type(evaled_type):
            return evaled_type

        # Everything remaining should be a raw annotation that needs to be turned into
        # a StrawberryType
        if self._is_enum(evaled_type):
            return self.create_enum(evaled_type)
        if self._is_list(evaled_type):
            return self.create_list(evaled_type)
        elif self._is_optional(evaled_type):
            return self.create_optional(evaled_type)
        elif self._is_union(evaled_type):
            return self.create_union(evaled_type)
        elif is_type_var(evaled_type):
            return self.create_type_var(evaled_type)

        # TODO: Raise exception now, or later?
        # ... raise NotImplementedError(f"Unknown type {evaled_type}")
        return evaled_type

    def create_concrete_type(self, evaled_type: type) -> type:
        if _is_object_type(evaled_type):
            type_definition: TypeDefinition
            type_definition = evaled_type._type_definition  # type: ignore
            return type_definition.resolve_generic(evaled_type)

        raise ValueError(f"Not supported {evaled_type}")

    def create_enum(self, evaled_type: Any) -> EnumDefinition:
        return evaled_type._enum_definition

    def create_list(self, evaled_type: Any) -> StrawberryList:
        of_type = StrawberryAnnotation(
            annotation=evaled_type.__args__[0],
            namespace=self.namespace,
        ).resolve()

        return StrawberryList(of_type)

    def create_optional(self, evaled_type: Any) -> StrawberryOptional:
        types = evaled_type.__args__
        non_optional_types = tuple(
            filter(
                lambda x: x is not type(None) and x is not type(UNSET),  # noqa: E721
                types,
            )
        )

        # Note that passing a single type to `Union` is equivalent to not using `Union`
        # at all. This allows us to not di any checks for how many types have been
        # passed as we can safely use `Union` for both optional types
        # (e.g. `Optional[str]`) and optional unions (e.g.
        # `Optional[Union[TypeA, TypeB]]`)
        child_type = Union[non_optional_types]  # type: ignore

        of_type = StrawberryAnnotation(
            annotation=child_type,
            namespace=self.namespace,
        ).resolve()

        return StrawberryOptional(of_type)

    def create_type_var(self, evaled_type: TypeVar) -> StrawberryTypeVar:
        return StrawberryTypeVar(evaled_type)

    def create_union(self, evaled_type) -> "StrawberryUnion":
        # Prevent import cycles
        from strawberry.union import StrawberryUnion

        # TODO: Deal with Forward References/origin
        if isinstance(evaled_type, StrawberryUnion):
            return evaled_type

        types = evaled_type.__args__
        union = StrawberryUnion(
            type_annotations=tuple(StrawberryAnnotation(type_) for type_ in types),
        )
        return union

    @classmethod
    def _is_async_type(cls, annotation: type) -> bool:
        origin = getattr(annotation, "__origin__", None)
        return origin in ASYNC_TYPES

    @classmethod
    def _is_enum(cls, annotation: Any) -> bool:
        # Type aliases are not types so we need to make sure annotation can go into
        # issubclass
        if not isinstance(annotation, type):
            return False
        return issubclass(annotation, Enum)

    @classmethod
    def _is_generic(cls, annotation: Any) -> bool:
        if hasattr(annotation, "__origin__"):
            return is_generic(annotation.__origin__)

        return False

    @classmethod
    def _is_lazy_type(cls, annotation: Any) -> bool:
        return isinstance(annotation, LazyType)

    @classmethod
    def _is_optional(cls, annotation: Any) -> bool:
        """Returns True if the annotation is Optional[SomeType]"""

        # Optionals are represented as unions
        if not cls._is_union(annotation):
            return False

        types = annotation.__args__

        # A Union to be optional needs to have at least one None type
        return any(x is type(None) for x in types)  # noqa: E721

    @classmethod
    def _is_list(cls, annotation: Any) -> bool:
        """Returns True if annotation is a List"""

        annotation_origin = getattr(annotation, "__origin__", None)

        return annotation_origin == list

    @classmethod
    def _is_strawberry_type(cls, evaled_type: Any) -> bool:
        # Prevent import cycles
        from strawberry.union import StrawberryUnion

        if isinstance(evaled_type, EnumDefinition):
            return True
        elif _is_input_type(evaled_type):  # TODO: Replace with StrawberryInputObject
            return True
        # TODO: add support for StrawberryInterface when implemented
        elif isinstance(evaled_type, StrawberryList):
            return True
        elif _is_object_type(evaled_type):  # TODO: Replace with StrawberryObject
            return True
        elif isinstance(evaled_type, TypeDefinition):
            return True
        elif isinstance(evaled_type, StrawberryOptional):
            return True
        elif isinstance(
            evaled_type, ScalarDefinition
        ):  # TODO: Replace with StrawberryScalar
            return True
        elif isinstance(evaled_type, StrawberryUnion):
            return True

        return False

    @classmethod
    def _is_union(cls, annotation: Any) -> bool:
        """Returns True if annotation is a Union"""

        # this check is needed because unions declared with the new syntax `A | B`
        # don't have a `__origin__` property on them, but they are instances of
        # `UnionType`, which is only available in Python 3.10+
        if sys.version_info >= (3, 10):
            from types import UnionType

            if isinstance(annotation, UnionType):
                return True

        # unions declared as Union[A, B] fall through to this check, even on python 3.10+

        annotation_origin = getattr(annotation, "__origin__", None)

        return annotation_origin is typing.Union

    @classmethod
    def _strip_async_type(cls, annotation) -> type:
        return annotation.__args__[0]

    @classmethod
    def _strip_lazy_type(cls, annotation: LazyType) -> type:
        return annotation.resolve_type()


################################################################################
# Temporary functions to be removed with new types
################################################################################


def _is_input_type(type_: Any) -> bool:
    if not _is_object_type(type_):
        return False

    return type_._type_definition.is_input


def _is_object_type(type_: Any) -> bool:
    # isinstance(type_, StrawberryObjectType)  # noqa: E800
    return hasattr(type_, "_type_definition")

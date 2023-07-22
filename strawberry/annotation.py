from __future__ import annotations

import logging
import sys
import typing
from collections import abc
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    ForwardRef,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Annotated, Self, get_args, get_origin

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.exceptions.not_a_strawberry_enum import NotAStrawberryEnumError
from strawberry.lazy_type import LazyType
from strawberry.private import is_private
from strawberry.type import (
    StrawberryList,
    StrawberryOptional,
    StrawberryTypeVar,
    has_object_definition,
)
from strawberry.types.types import StrawberryObjectDefinition
from strawberry.unset import UNSET
from strawberry.utils.typing import eval_type, is_generic, is_type_var

if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.type import StrawberryType
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
    __slots__ = "raw_annotation", "namespace", "__eval_cache__"

    def __init__(
        self,
        annotation: Union[object, str],
        *,
        namespace: Optional[Dict[str, Any]] = None,
    ):
        self.raw_annotation = annotation
        self.namespace = namespace

        self.__eval_cache__: Optional[Type[Any]] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StrawberryAnnotation):
            return NotImplemented

        return self.resolve() == other.resolve()

    def __hash__(self) -> int:
        return hash(self.resolve())

    @staticmethod
    def from_annotation(
        annotation: object, namespace: Optional[Dict[str, Any]] = None
    ) -> Optional[StrawberryAnnotation]:
        if annotation is None:
            return None

        if not isinstance(annotation, StrawberryAnnotation):
            return StrawberryAnnotation(annotation, namespace=namespace)
        return annotation

    @property
    def annotation(self) -> Union[object, str]:
        """Return evaluated type on success or fallback to raw (string) annotation."""
        try:
            return self.evaluate()
        except NameError:
            # Evaluation failures can happen when importing types within a TYPE_CHECKING
            # block or if the type is declared later on in a module.
            return self.raw_annotation

    @annotation.setter
    def annotation(self, value: Union[object, str]) -> None:
        self.raw_annotation = value

    def evaluate(self) -> type:
        """Return evaluated annotation using `strawberry.util.typing.eval_type`."""
        evaled_type = self.__eval_cache__
        if evaled_type:
            return evaled_type

        annotation = self.raw_annotation
        if isinstance(annotation, str):
            annotation = ForwardRef(annotation)

        evaled_type = eval_type(annotation, self.namespace, None)

        self.__eval_cache__ = evaled_type
        return evaled_type

    def resolve(self) -> Union[StrawberryType, type]:
        """Return resolved (transformed) annotation."""
        evaled_type = cast(Any, self.evaluate())

        if is_private(evaled_type):
            return evaled_type

        args: List[Any] = []
        if get_origin(evaled_type) is Annotated:
            evaled_type, *args = get_args(evaled_type)

        if self._is_async_type(evaled_type):
            evaled_type = self._strip_async_type(evaled_type)
        if self._is_lazy_type(evaled_type):
            return evaled_type

        if self._is_generic(evaled_type):
            if any(is_type_var(type_) for type_ in get_args(evaled_type)):
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
            return self.create_union(evaled_type, args)
        elif is_type_var(evaled_type) or evaled_type is Self:
            return self.create_type_var(cast(TypeVar, evaled_type))

        # TODO: Raise exception now, or later?
        # ... raise NotImplementedError(f"Unknown type {evaled_type}")
        return evaled_type

    def set_namespace_from_field(self, field: StrawberryField) -> None:
        module = sys.modules[field.origin.__module__]
        self.namespace = module.__dict__

        self.__eval_cache__ = None  # Invalidate cache to allow re-evaluation

    def create_concrete_type(self, evaled_type: type) -> type:
        if has_object_definition(evaled_type):
            return evaled_type.__strawberry_definition__.resolve_generic(evaled_type)
        raise ValueError(f"Not supported {evaled_type}")

    def create_enum(self, evaled_type: Any) -> EnumDefinition:
        try:
            return evaled_type._enum_definition
        except AttributeError:
            raise NotAStrawberryEnumError(evaled_type)

    def create_list(self, evaled_type: Any) -> StrawberryList:
        item_type, *_ = get_args(evaled_type)
        of_type = StrawberryAnnotation(
            annotation=item_type,
            namespace=self.namespace,
        ).resolve()

        return StrawberryList(of_type)

    def create_optional(self, evaled_type: Any) -> StrawberryOptional:
        types = get_args(evaled_type)
        non_optional_types = tuple(
            filter(
                lambda x: x is not type(None) and x is not type(UNSET),
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

    def create_union(self, evaled_type: Type[Any], args: list[Any]) -> StrawberryUnion:
        # Prevent import cycles
        from strawberry.union import StrawberryUnion

        # TODO: Deal with Forward References/origin
        if isinstance(evaled_type, StrawberryUnion):
            return evaled_type

        types = get_args(evaled_type)

        union = StrawberryUnion(
            type_annotations=tuple(StrawberryAnnotation(type_) for type_ in types),
        )

        union_args = [arg for arg in args if isinstance(arg, StrawberryUnion)]
        if len(union_args) > 1:
            logging.warning(
                "Duplicate union definition detected. "
                "Only the first definition will be considered"
            )

        if union_args:
            arg = union_args[0]
            union.graphql_name = arg.graphql_name
            union.description = arg.description
            union.directives = arg.directives

            union._source_file = arg._source_file
            union._source_line = arg._source_line

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

        types = get_args(annotation)

        # A Union to be optional needs to have at least one None type
        return any(x is type(None) for x in types)

    @classmethod
    def _is_list(cls, annotation: Any) -> bool:
        """Returns True if annotation is a List"""

        annotation_origin = get_origin(annotation)

        return (annotation_origin in (list, tuple)) or annotation_origin is abc.Sequence

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
        elif has_object_definition(evaled_type):
            return True
        elif isinstance(evaled_type, StrawberryObjectDefinition):
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

        # unions declared as Union[A, B] fall through to this check
        # even on python 3.10+

        annotation_origin = getattr(annotation, "__origin__", None)

        return annotation_origin is typing.Union

    @classmethod
    def _strip_async_type(cls, annotation: Type) -> type:
        return annotation.__args__[0]

    @classmethod
    def _strip_lazy_type(cls, annotation: LazyType) -> type:
        return annotation.resolve_type()


################################################################################
# Temporary functions to be removed with new types
################################################################################


def _is_input_type(type_: Any) -> bool:
    if not has_object_definition(type_):
        return False

    return type_.__strawberry_definition__.is_input

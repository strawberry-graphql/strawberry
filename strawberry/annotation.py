import typing
from enum import Enum
from typing import Dict, ForwardRef, Union, _eval_type, _SpecialGenericAlias, Optional, Type

from strawberry.custom_scalar import SCALAR_REGISTRY, ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.scalars import SCALAR_TYPES
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType


ListType = _SpecialGenericAlias
UnionType = _SpecialGenericAlias


class StrawberryAnnotation:
    def __init__(self, annotation: Union[object, str], *, namespace: Optional[Dict] = None):
        self.annotation = annotation
        self.namespace = namespace

    def resolve(self) -> Union[StrawberryType, type]:

        if isinstance(self.annotation, str):
            annotation = ForwardRef(self.annotation)
        else:
            annotation = self.annotation

        evaled_type = _eval_type(annotation, self.namespace, None)

        if self._is_enum(evaled_type):
            return self.create_enum(evaled_type)
        if self._is_list(evaled_type):
            return self.create_list(evaled_type)
        elif self._is_optional(evaled_type):
            return self.create_optional(evaled_type)
        elif self._is_scalar(evaled_type):
            return evaled_type

        return evaled_type

    def create_enum(self, evaled_type: Type[Enum]) -> EnumDefinition:
        return evaled_type._enum_definition

    def create_list(self, evaled_type: ListType) -> StrawberryList:
        of_type = StrawberryAnnotation(
            annotation=evaled_type.__args__[0],
            namespace=self.namespace,
        ).resolve()

        return StrawberryList(of_type)

    def create_optional(self, evaled_type: UnionType) -> StrawberryOptional:
        types = evaled_type.__args__
        non_optional_types = tuple(filter(lambda x: x is not type(None), types))

        # Note that this returns _not_ a Union if len(non_optional_types) == 1
        child_type = Union[non_optional_types]

        of_type = StrawberryAnnotation(
            annotation=child_type,
            namespace=self.namespace,
        ).resolve()

        return StrawberryOptional(of_type)

    def create_scalar(self, evaled_type: ...):
        if evaled_type in SCALAR_REGISTRY:
            # TODO: What is stored here? Would evaled_type ever be in the registry?
            return SCALAR_REGISTRY[evaled_type]

        if evaled_type in SCALAR_TYPES:
            return StrawberryType.from_type(evaled_type)

        # TODO: Should we ever be creating a Scalar type here?
        raise NotImplementedError

    @classmethod
    def _is_enum(cls, annotation: type) -> bool:
        return issubclass(annotation, Enum)

    @classmethod
    def _is_optional(cls, annotation: type) -> bool:
        """Returns True if the annotation is Optional[SomeType]"""

        # Optionals are represented as unions
        if not cls._is_union(annotation):
            return False

        annotation = typing.cast(UnionType, annotation)
        types = annotation.__args__

        # A Union to be optional needs to have at least one None type
        return any(x is type(None) for x in types)

    @classmethod
    def _is_list(cls, annotation: type) -> bool:
        """Returns True if annotation is a List"""

        annotation_origin = getattr(annotation, "__origin__", None)

        return annotation_origin == list

    @classmethod
    def _is_scalar(cls, annotation: type) -> bool:
        type_ = getattr(annotation, "__supertype__", annotation)

        if type_ in SCALAR_REGISTRY:
            return True

        if type_ in SCALAR_TYPES:
            return True

        return hasattr(annotation, "_scalar_definition")

    @classmethod
    def _is_union(cls, annotation: type) -> bool:
        """Returns True if annotation is a Union"""

        annotation_origin = getattr(annotation, "__origin__", None)

        return annotation_origin is typing.Union

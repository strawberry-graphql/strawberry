from __future__ import annotations

import dataclasses
import warnings
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)
from typing_extensions import TypeVar

from .nodes import convert_selections

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo, OperationDefinitionNode
    from graphql.language import FieldNode
    from graphql.pyutils.path import Path

    from strawberry.arguments import StrawberryArgument
    from strawberry.field import StrawberryField
    from strawberry.schema import Schema
    from strawberry.type import StrawberryType, WithStrawberryObjectDefinition

    from .nodes import Selection

ContextType = TypeVar("ContextType", default=Any)
RootValueType = TypeVar("RootValueType", default=Any)


@dataclasses.dataclass
class Info(Generic[ContextType, RootValueType]):
    _raw_info: GraphQLResolveInfo
    _field: StrawberryField

    def __class_getitem__(cls, types: Union[type, Tuple[type, ...]]) -> Type[Info]:
        """Workaround for when passing only one type.

        Python doesn't yet support directly passing only one type to a generic class
        that has typevars with defaults. This is a workaround for that.

        See:
        https://discuss.python.org/t/passing-only-one-typevar-of-two-when-using-defaults/49134
        """

        if not isinstance(types, tuple):
            types = (types, Any)  # type: ignore

        return super().__class_getitem__(types)  # type: ignore

    @property
    def field_name(self) -> str:
        return self._raw_info.field_name

    @property
    def schema(self) -> Schema:
        return self._raw_info.schema._strawberry_schema  # type: ignore

    @property
    def field_nodes(self) -> List[FieldNode]:  # deprecated
        warnings.warn(
            "`info.field_nodes` is deprecated, use `selected_fields` instead",
            DeprecationWarning,
            stacklevel=2,
        )

        return self._raw_info.field_nodes

    @cached_property
    def selected_fields(self) -> List[Selection]:
        info = self._raw_info
        return convert_selections(info, info.field_nodes)

    @property
    def context(self) -> ContextType:
        return self._raw_info.context

    @property
    def root_value(self) -> RootValueType:
        return self._raw_info.root_value

    @property
    def variable_values(self) -> Dict[str, Any]:
        return self._raw_info.variable_values

    @property
    def return_type(
        self,
    ) -> Optional[Union[Type[WithStrawberryObjectDefinition], StrawberryType]]:
        return self._field.type

    @property
    def python_name(self) -> str:
        return self._field.python_name

    # TODO: create an abstraction on these fields
    @property
    def operation(self) -> OperationDefinitionNode:
        return self._raw_info.operation

    @property
    def path(self) -> Path:
        return self._raw_info.path

    # TODO: parent_type as strawberry types

    # Helper functions
    def get_argument_definition(self, name: str) -> Optional[StrawberryArgument]:
        """
        Get the StrawberryArgument definition for the current field by name.
        """
        try:
            return next(arg for arg in self._field.arguments if arg.python_name == name)
        except StopIteration:
            return None

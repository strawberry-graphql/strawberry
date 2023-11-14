from __future__ import annotations

import functools
from enum import Enum
from typing import Any, Dict, Hashable, Optional, Tuple
from typing_extensions import Protocol

from graphql.type import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLType,
    GraphQLUnionType,
    GraphQLWrappingType,
)

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.field import StrawberryField
from strawberry.type import StrawberryList, StrawberryType
from strawberry.types.types import StrawberryObjectDefinition
from strawberry.union import StrawberryUnion


class _ScalarRegistry:
    """A simple type registry for the GraphQLScalars that we encounter."""

    def __init__(self) -> None:
        self._cache: Dict[Any, Tuple[bool, Optional[ScalarDefinition]]] = {}

    def _check_populate_cache(
        self, obj: Hashable
    ) -> Tuple[bool, Optional[ScalarDefinition]]:
        if obj in self._cache:
            return self._cache[obj]

        is_scalar = False
        if isinstance(obj, GraphQLNonNull) and isinstance(
            obj.of_type, GraphQLScalarType
        ):
            is_scalar = True
        elif isinstance(obj, GraphQLScalarType):
            is_scalar = True
            scalar_def = ScalarDefinition(
                name=obj.name,
                description=obj.description,
                specified_by_url=obj.specified_by_url,
                serialize=obj.serialize,
                parse_value=obj.parse_value,
                parse_literal=obj.parse_literal,
            )

        else:
            scalar_def = None
        if not is_scalar:
            self._cache[obj] = (False, None)
        self._cache[obj] = (is_scalar, scalar_def)
        return self._cache[obj]

    def __contains__(self, obj: Hashable) -> bool:
        return self._check_populate_cache(obj)[0]

    def __getitem__(self, obj: Hashable) -> ScalarDefinition:
        _, result = self._check_populate_cache(obj)
        if result is None:
            raise KeyError(obj)
        return result


class DeferredTypeStrawberryField(StrawberryField):
    """A basic strawberry field subclass for deferred resolution of the type property."""

    def __init__(
        self,
        graphql_field_type: GraphQLOutputType,
        schema_wrapper: GraphQLSchemaWrapper,
        **kwargs: Any,
    ):
        self.graphql_field_type = graphql_field_type
        self.schema_wrapper = schema_wrapper
        super().__init__(**kwargs)

    @property
    def type(self) -> Any:
        inner_type = self.graphql_field_type
        while isinstance(inner_type, GraphQLWrappingType):
            inner_type = inner_type.of_type

        name = getattr(inner_type, "name", None)
        if name is not None:
            field_type = self.schema_wrapper.get_type_by_name(name)
        else:
            raise ValueError(f"Unable to find type for {self.graphql_field_type}")
        return field_type

    @type.setter
    def type(self, val: Any) -> None:
        ...


class GraphQLSchemaWrapper:
    def __init__(self, schema: GraphQLSchema) -> None:
        self.schema = schema
        self.scalar_registry = _ScalarRegistry()
        self._types_by_name: dict[str, Optional[StrawberryType]] = {}

        def get_field_for_type(
            field_name: str, type_name: str
        ) -> Optional[StrawberryField]:
            return self._get_field_for_type(field_name, type_name)

        self.get_field_for_type = functools.lru_cache(maxsize=None)(get_field_for_type)

    def get_type_by_name(self, name: str) -> Optional[StrawberryType]:
        if name not in self._types_by_name:
            self._types_by_name[name] = self._get_type_by_name(name)

        return self._types_by_name[name]

    def _get_type_by_name(self, name: str) -> Optional[StrawberryType]:
        schema_type = self.schema.get_type(name)
        if schema_type is None:
            return None
        return self._strawberry_type_from_graphql_type(schema_type)

    def _strawberry_type_from_graphql_type(
        self, graphql_type: GraphQLType
    ) -> StrawberryType:
        if isinstance(graphql_type, GraphQLNonNull):
            graphql_type = graphql_type.of_type
        if isinstance(graphql_type, GraphQLEnumType):
            wrapped_cls = Enum("name", list(graphql_type.values))  # type: ignore[misc]
            return EnumDefinition(
                wrapped_cls=wrapped_cls,
                name=graphql_type.name,
                values=[
                    EnumValue(name=name, value=i)
                    for i, name in enumerate(graphql_type.values)
                ],
                description=None,
            )
        if isinstance(
            graphql_type,
            (GraphQLObjectType, GraphQLInputObjectType, GraphQLInterfaceType),
        ):
            obj_def = StrawberryObjectDefinition(
                name=graphql_type.name,
                is_input=False,
                is_interface=False,
                interfaces=[],
                description=graphql_type.description,
                origin=type(graphql_type.name, (), {}),
                extend=False,
                directives=[],
                is_type_of=None,
                resolve_type=None,
                fields=[],
            )
            for graphql_field in graphql_type.fields.values():
                obj_def.fields.append(
                    self._strawberry_field_from_graphql_field(graphql_field)
                )
            # This is just monkey-patching the strawberry-definition with itself.
            obj_def.__strawberry_definition__ = obj_def  # type:ignore[attr-defined]
            return obj_def
        if isinstance(graphql_type, GraphQLScalarType):
            return self.scalar_registry[graphql_type]
        if isinstance(graphql_type, GraphQLList):
            return StrawberryList(
                of_type=self._strawberry_type_from_graphql_type(graphql_type.of_type)
            )
        if isinstance(graphql_type, GraphQLUnionType):
            types = [self.get_type_by_name(type_.name) for type_ in graphql_type.types]
            return StrawberryUnion(
                name=graphql_type.name, type_annotations=tuple(types)
            )
        raise ValueError(graphql_type)

    def _strawberry_field_from_graphql_field(
        self, graphql_field: GraphQLField
    ) -> StrawberryField:
        ast_node = graphql_field.ast_node
        if ast_node is None:
            raise ValueError("GraphQLField must have an AST node to get it's name.")
        name = ast_node.name.value
        return DeferredTypeStrawberryField(
            graphql_field_type=graphql_field.type,
            schema_wrapper=self,
            python_name=name,
            graphql_name=name,
        )

    @property
    def schema_converter(self) -> GraphQLSchemaWrapper:
        return self

    def _get_field_for_type(
        self, field_name: str, type_name: str
    ) -> Optional[StrawberryField]:
        type_ = self.get_type_by_name(type_name)
        if type_ is None:
            return None
        if not isinstance(type_, StrawberryObjectDefinition):
            raise TypeError(f"{type_name!r} does not correspond to an object type!")
        return self.get_field(type_, field_name)

    def get_field(
        self, parent_type: StrawberryObjectDefinition, field_name: str
    ) -> Optional[StrawberryField]:
        """Get field of a given type with the given name."""
        if field_name == "__typename":
            field = StrawberryField(python_name=field_name, graphql_name=field_name)
            field.type = self.get_type_by_name("String")
            return field

        return next(fld for fld in parent_type.fields if fld.name == field_name)


class Registry(Protocol):
    def __contains__(self, key: Hashable) -> bool:
        ...

    def __getitem__(self, key: Hashable) -> Any:
        ...


class SchemaConverterLike(Protocol):
    @property
    def scalar_registry(self) -> Registry:
        ...


class SchemaLike(Protocol):
    @property
    def schema_converter(self) -> SchemaConverterLike:
        ...

    def get_type_by_name(self, name: str) -> Optional[StrawberryType]:
        ...

    def get_field_for_type(
        self, field_name: str, type_name: str
    ) -> Optional[StrawberryField]:
        ...

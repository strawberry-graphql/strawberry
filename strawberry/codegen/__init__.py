from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Type, Union, cast

from typing_extensions import Protocol

from graphql import (
    FieldNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    parse,
)

import strawberry
from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.type import (
    StrawberryContainer,
    StrawberryList,
    StrawberryOptional,
    StrawberryType,
)
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.str_converters import capitalize_first, to_camel_case


class HasSelectionSet(Protocol):
    selection_set: Optional[SelectionSetNode]


@dataclass
class GraphQLOptional:
    of_type: GraphQLType


@dataclass
class GraphQLList:
    of_type: GraphQLType


@dataclass
class GraphQLUnion:
    name: str
    types: List[GraphQLObjectType]


@dataclass
class GraphQLField:
    name: str
    type: GraphQLType


@dataclass
class GraphQLObjectType:
    name: str
    fields: List[GraphQLField]


@dataclass
class GraphQLEnum:
    name: str
    values: List[str]


@dataclass
class GraphQLScalar:
    name: str
    python_type: Type


GraphQLType = Union[
    GraphQLObjectType,
    GraphQLEnum,
    GraphQLScalar,
    GraphQLOptional,
    GraphQLList,
    GraphQLUnion,
]


class CodegenPlugin:
    def on_union(self) -> None:
        ...

    def on_enum(self) -> None:
        ...

    def on_optional(self) -> None:
        ...

    def on_list(self) -> None:
        ...

    def on_scalar(self) -> None:
        ...

    def print(self, types: List[GraphQLType]) -> str:
        return ""


class QueryCodegenPluginManager:
    def __init__(self, plugins: List[CodegenPlugin]) -> None:
        self.plugins = plugins

    def on_union(self) -> None:
        for plugin in self.plugins:
            plugin.on_union()

    def on_enum(self) -> None:
        for plugin in self.plugins:
            plugin.on_enum()

    def on_optional(self) -> None:
        for plugin in self.plugins:
            plugin.on_optional()

    def on_list(self) -> None:
        for plugin in self.plugins:
            plugin.on_list()

    def on_scalar(self) -> None:
        for plugin in self.plugins:
            plugin.on_scalar()

    def print(self, types: List[GraphQLType]) -> str:
        return "\n\n".join(plugin.print(types) for plugin in self.plugins)


class QueryCodegen:
    def __init__(self, schema: strawberry.Schema, plugins: List[CodegenPlugin]):
        self.schema = schema
        self.plugin_manager = QueryCodegenPluginManager(plugins)
        self.types: List[GraphQLType] = []

    def codegen(self, query: str) -> str:
        ast = parse(query)

        # assuming we have one document definition
        # TODO: throw error if there are multiple definitions
        operation = ast.definitions[0]
        # TODO: convert these in nice errors
        assert isinstance(operation, OperationDefinitionNode)
        assert operation.name is not None

        operation_name = operation.name.value

        result_class_name = f"{operation_name}Result"

        query_type = self.schema.get_type_by_name("Query")

        assert isinstance(query_type, TypeDefinition)

        self._collect_types(
            operation,
            parent_type=query_type,
            class_name=result_class_name,
        )

        return self.print()

    def _get_field_type(
        self,
        field_type: Union[StrawberryType, type],
    ) -> GraphQLType:
        if isinstance(field_type, StrawberryOptional):
            return GraphQLOptional(self._get_field_type(field_type.of_type))

        if isinstance(field_type, StrawberryList):
            return GraphQLList(self._get_field_type(field_type.of_type))

        if (
            not isinstance(field_type, StrawberryType)
            and field_type in self.schema.schema_converter.scalar_registry
        ):
            field_type = self.schema.schema_converter.scalar_registry[field_type]

        if isinstance(field_type, ScalarWrapper):
            python_type = field_type.wrap
            if hasattr(python_type, "__supertype__"):
                python_type = python_type.__supertype__  # type: ignore

            return self._collect_scalar(field_type._scalar_definition, python_type)

        if isinstance(field_type, ScalarDefinition):
            return self._collect_scalar(field_type, None)

        elif isinstance(field_type, EnumDefinition):
            return self._collect_enum(field_type)

        assert False, field_type

    def _field_from_selection(
        self, selection: FieldNode, parent_type: TypeDefinition
    ) -> GraphQLField:
        field = self.schema.get_field_for_type(selection.name.value, parent_type.name)
        assert field

        field_type = self._get_field_type(field.type)

        return GraphQLField(field.name, field_type)

    # def _get_field_with_subselection(selection: FieldNode) -> GraphQLField:

    def _field_from_selection_set(
        self, selection: FieldNode, class_name: str, parent_type: TypeDefinition
    ) -> GraphQLField:
        assert selection.selection_set is not None

        selected_field = self.schema.get_field_for_type(
            selection.name.value, parent_type.name
        )
        assert selected_field

        selected_field_type = selected_field.type

        while isinstance(selected_field_type, StrawberryContainer):
            selected_field_type = selected_field_type.of_type

        if isinstance(selected_field_type, StrawberryUnion):
            # TODO: remove duplication
            name = capitalize_first(to_camel_case(selection.name.value))
            class_name = f"{class_name}{name}"

            sub_types = self._collect_types_using_fragments(
                selection, parent_type, class_name
            )

            union = GraphQLUnion(class_name, sub_types)

            self.types.append(union)

            return GraphQLField(selection.name.value, union)

        parent_type = cast(
            TypeDefinition, selected_field_type._type_definition  # type: ignore
        )

        name = capitalize_first(to_camel_case(selection.name.value))
        class_name = f"{class_name}{(name)}"
        field_type = self._collect_types(selection, parent_type, class_name)

        selected_field_type = selected_field.type

        # TODO: this is ugly :D

        while isinstance(selected_field_type, StrawberryContainer):
            # TODO: this doesn't support lists :'D
            field_type = GraphQLOptional(field_type)

            selected_field_type = selected_field_type.of_type

        return GraphQLField(selected_field.name, field_type)

    def _get_field(
        self, selection: FieldNode, class_name: str, parent_type: TypeDefinition
    ) -> GraphQLField:

        if selection.selection_set:
            return self._field_from_selection_set(selection, class_name, parent_type)

        return self._field_from_selection(selection, parent_type)

    def _collect_types_with_inline_fragments(
        self,
        selection: SelectionNode,
        parent_type: TypeDefinition,
        class_name: str,
    ) -> Union[GraphQLObjectType, GraphQLUnion]:
        sub_types = self._collect_types_using_fragments(
            selection, parent_type, class_name
        )

        if len(sub_types) == 1:
            return sub_types[0]

        union = GraphQLUnion(class_name, sub_types)

        self.types.append(union)

        return union

    def _collect_types(
        self,
        selection: HasSelectionSet,
        parent_type: TypeDefinition,
        class_name: str,
    ) -> GraphQLType:
        assert selection.selection_set is not None
        selection_set = selection.selection_set

        if any(
            isinstance(selection, InlineFragmentNode)
            for selection in selection_set.selections
        ):
            return self._collect_types_with_inline_fragments(
                selection, parent_type, class_name
            )

        current_type = GraphQLObjectType(class_name, [])

        for selection in selection_set.selections:
            assert isinstance(selection, FieldNode)

            field = self._get_field(selection, class_name, parent_type)

            current_type.fields.append(field)

        self.types.append(current_type)

        return current_type

    def print(self) -> str:
        return self.plugin_manager.print(self.types)

    def _collect_types_using_fragments(
        self,
        selection: HasSelectionSet,
        parent_type: TypeDefinition,
        class_name: str,
    ) -> List[GraphQLObjectType]:
        assert selection.selection_set

        common_fields: List[GraphQLField] = []
        fragments: List[InlineFragmentNode] = []
        sub_types: List[GraphQLObjectType] = []

        for sub_selection in selection.selection_set.selections:
            if isinstance(sub_selection, FieldNode):
                common_fields.append(
                    self._get_field(sub_selection, class_name, parent_type)
                )

            if isinstance(sub_selection, InlineFragmentNode):
                fragments.append(sub_selection)

        for fragment in fragments:
            fragment_class_name = class_name + fragment.type_condition.name.value
            current_type = GraphQLObjectType(fragment_class_name, [])

            for sub_selection in fragment.selection_set.selections:
                # TODO: recurse, use existing method ?
                assert isinstance(sub_selection, FieldNode)

                current_type.fields = list(common_fields)

                parent_type = self.schema.get_type_by_name(
                    fragment.type_condition.name.value
                )

                assert parent_type

                current_type.fields.append(
                    self._get_field(
                        selection=sub_selection,
                        class_name=fragment_class_name,
                        parent_type=parent_type,
                    )
                )

            sub_types.append(current_type)

        self.types.extend(sub_types)

        return sub_types

    def _collect_scalar(
        self, scalar_definition: ScalarDefinition, python_type: Type
    ) -> GraphQLScalar:
        graphql_scalar = GraphQLScalar(scalar_definition.name, python_type=python_type)
        self.plugin_manager.on_scalar()

        self.types.append(graphql_scalar)

        return graphql_scalar

    def _collect_enum(self, enum: EnumDefinition) -> GraphQLEnum:
        self.plugin_manager.on_enum()
        graphql_enum = GraphQLEnum(enum.name, [value.value for value in enum.values])
        self.types.append(graphql_enum)
        return graphql_enum

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Union

from graphql import (
    FieldNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
    parse,
)

import strawberry
from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.union import StrawberryUnion
from strawberry.utils.str_converters import capitalize_first, to_camel_case


@dataclass
class GraphQLOptional:
    of_type: GraphQLType


@dataclass
class GraphQLList:
    of_type: GraphQLType


@dataclass
class GraphQLUnion:
    types: List[GraphQLObjectType]
    name: str


@dataclass
class GraphQLField:
    name: str
    type: GraphQLType


@dataclass
class GraphQLObjectType:
    name: str
    kind: str
    fields: List[GraphQLField]


@dataclass
class GraphQLEnum:
    name: str
    values: List[str]


@dataclass
class GraphQLScalar:
    name: str
    type: str


GraphQLType = Union[
    GraphQLObjectType,
    GraphQLEnum,
    GraphQLScalar,
    GraphQLOptional,
    GraphQLList,
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

    def codegen(self, query: str) -> str:
        ast = parse(query)

        # assuming we have document definition
        operation = ast.definitions[0]
        # TODO: convert these in nice errors
        assert isinstance(operation, OperationDefinitionNode)
        assert operation.name is not None

        operation_name = operation.name.value

        result_class_name = f"{operation_name}Result"

        types = self._collect_types(
            operation.selection_set,
            parent_type="Query",
            class_name=result_class_name,
        )

        return self.print(types)

    def print(self, types: List[GraphQLType]) -> str:
        return self.plugin_manager.print(types)

    def _collect_inline_fragment(
        self,
        fragment: InlineFragmentNode,
        class_name: str,
        types: List,
    ) -> GraphQLObjectType:
        class_name += fragment.type_condition.name.value
        current_type = GraphQLObjectType(class_name, "ObjectType", [])

        for selection in fragment.selection_set.selections:
            assert isinstance(selection, FieldNode)

            current_type.fields.append(
                self._collect_field(
                    selection=selection,
                    class_name=class_name,
                    parent_type=fragment.type_condition.name.value,
                    types=types,
                )
            )

        return current_type

    def _collect_field(
        self,
        selection: FieldNode,
        class_name: str,
        parent_type: str,
        types: List,
    ) -> GraphQLField:

        field = self.schema.get_field_for_type(selection.name.value, parent_type)
        assert field is not None, f"{selection.name.value} {parent_type}"

        # field_type, unwrapped_type = self._get_type_name(field_type)
        name = capitalize_first(to_camel_case(selection.name.value))
        field_type_ = f"{class_name}{name}"

        field_type = field.type

        if (
            not isinstance(field_type, StrawberryType)
            and field_type in self.schema.schema_converter.scalar_registry
        ):
            field_type = self.schema.schema_converter.scalar_registry[field_type]

        if isinstance(field_type, ScalarDefinition):
            field_type = self._collect_scalar(field_type, types, class_name=field_type_)

        # if isinstance(field_type, ScalarWrapper):
        #     field_type = self._collect_scalar(field_type, types, class_name=field_type_)

        elif isinstance(field_type, EnumDefinition):
            field_type = self._collect_enum(field_type, types, class_name=field_type_)
            # field_type = (
            #     GraphQLEnum()
            # )  # field_type.replace(unwrapped_type, field_type_)

        if selection.selection_set:
            sub_types = self._collect_types(
                selection.selection_set,
                unwrapped_type,
                class_name=field_type_,
                types=types,
            )

            field_type = field_type.replace(unwrapped_type, field_type_)

            if len(sub_types) > 1 and isinstance(field_type, StrawberryUnion):
                self.plugin_manager.on_union()

                assert all(isinstance(t, GraphQLObjectType) for t in sub_types)

                field_type = GraphQLUnion(name="TODO", types=sub_types)

        print(field_type)

        return GraphQLField(field.name, field_type)

    def _collect_types_using_fragments(
        self,
        selection_set: SelectionSetNode,
        parent_type: str,
        class_name: str,
        types: List[GraphQLType],
    ) -> List:
        common_fields: List[GraphQLField] = []
        fragments: List[InlineFragmentNode] = []
        sub_types: List[GraphQLObjectType] = []

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                common_fields.append(
                    self._collect_field(
                        selection=selection,
                        class_name=class_name,
                        parent_type=parent_type,
                        types=[],
                    )
                )

            if isinstance(selection, InlineFragmentNode):
                fragments.append(selection)

        for fragment in fragments:
            fragment_class_name = class_name + fragment.type_condition.name.value
            current_type = GraphQLObjectType(fragment_class_name, "ObjectType", [])

            for selection in fragment.selection_set.selections:
                # TODO: recurse, use existing method ?
                assert isinstance(selection, FieldNode)

                current_type.fields = list(common_fields)

                current_type.fields.append(
                    self._collect_field(
                        selection=selection,
                        class_name=fragment_class_name,
                        parent_type=fragment.type_condition.name.value,
                        types=[],
                    )
                )

            sub_types.append(current_type)

        types.extend(sub_types)

        return sub_types

    def _collect_types(
        self,
        selection_set: SelectionSetNode,
        parent_type: str,
        class_name: str,
        types: List = None,
    ) -> List[GraphQLType]:
        if types is None:
            types = []

        if any(
            isinstance(selection, InlineFragmentNode)
            for selection in selection_set.selections
        ):
            return self._collect_types_using_fragments(
                selection_set=selection_set,
                parent_type=parent_type,
                class_name=class_name,
                types=types,
            )

        current_type = GraphQLObjectType(class_name, "ObjectType", [])

        for selection in selection_set.selections:
            assert isinstance(selection, FieldNode)

            current_type.fields.append(
                self._collect_field(
                    selection=selection,
                    class_name=class_name,
                    parent_type=parent_type,
                    types=types,
                )
            )

        types.append(current_type)

        return types

    def _collect_scalar(
        self, scalar_definition: ScalarDefinition, types: List, class_name: str
    ) -> GraphQLScalar:
        # type_name = self._get_type_name(scalar.wrap)[0]

        graphql_scalar = GraphQLScalar(scalar_definition.name, scalar_definition.name)
        self.plugin_manager.on_scalar()

        types.append(graphql_scalar)

        return graphql_scalar

    def _collect_enum(
        self, enum: EnumDefinition, types: List, class_name: str
    ) -> GraphQLEnum:
        self.plugin_manager.on_enum()

        # TODO: enum don't really need to have a custom name as they are unique
        graphql_enum = GraphQLEnum(class_name, [value.value for value in enum.values])
        types.append(graphql_enum)
        return graphql_enum

    def _get_type_name(
        self, field_type: Union[StrawberryType, type]
    ) -> Tuple[str, str]:
        # support for NewType
        if hasattr(field_type, "__supertype__"):
            return self._get_type_name(field_type.__supertype__)  # type: ignore

        if isinstance(field_type, ScalarWrapper):
            return (
                field_type._scalar_definition.name,
                field_type._scalar_definition.name,
            )

        if not isinstance(field_type, StrawberryType):
            return field_type.__name__, field_type.__name__

        if isinstance(field_type, (StrawberryList, StrawberryOptional)):
            type_name, unwrapped_type = self._get_type_name(field_type.of_type)
            container_class = type(field_type)

            wrapper_name = {
                StrawberryList: "List",
                StrawberryOptional: "Optional",
            }[container_class]

            if wrapper_name == "Optional":
                self.plugin_manager.on_optional()
            else:
                self.plugin_manager.on_list()

            return f"{wrapper_name}[{type_name}]", unwrapped_type

        if isinstance(field_type, EnumDefinition):
            return field_type.name, field_type.name

        return "TODO", "TODO"

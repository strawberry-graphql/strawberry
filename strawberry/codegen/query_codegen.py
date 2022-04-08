from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple, Type, Union, cast

from typing_extensions import Literal, Protocol

from graphql import (
    ArgumentNode,
    BooleanValueNode,
    DirectiveNode,
    DocumentNode,
    EnumValueNode,
    FieldNode,
    InlineFragmentNode,
    IntValueNode,
    ListTypeNode,
    ListValueNode,
    NamedTypeNode,
    NonNullTypeNode,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    StringValueNode,
    TypeNode,
    ValueNode,
    VariableDefinitionNode,
    VariableNode,
    parse,
)

import strawberry
from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.str_converters import capitalize_first, to_camel_case

from .exceptions import (
    MultipleOperationsProvidedError,
    NoOperationNameProvidedError,
    NoOperationProvidedError,
)
from .types import (
    GraphQLArgument,
    GraphQLArgumentValue,
    GraphQLBoolValue,
    GraphQLDirective,
    GraphQLEnum,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFieldSelection,
    GraphQLInlineFragment,
    GraphQLIntValue,
    GraphQLList,
    GraphQLListValue,
    GraphQLObjectType,
    GraphQLOperation,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLSelection,
    GraphQLStringValue,
    GraphQLType,
    GraphQLUnion,
    GraphQLVariable,
    GraphQLVariableReference,
)


@dataclass
class CodegenFile:
    path: str
    content: str


@dataclass
class CodegenResult:
    files: List[CodegenFile]

    def to_string(self) -> str:
        return "\n".join(f.content for f in self.files) + "\n"

    def write(self, folder: Path) -> None:
        for file in self.files:
            destination = folder / file.path
            destination.write_text(file.content)


class HasSelectionSet(Protocol):
    selection_set: Optional[SelectionSetNode]


class QueryCodegenPlugin:
    def on_start(self) -> None:
        ...

    def on_end(self, result: CodegenResult) -> None:
        ...

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        return []


class QueryCodegenPluginManager:
    def __init__(self, plugins: List[QueryCodegenPlugin]) -> None:
        self.plugins = plugins

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> CodegenResult:
        result = CodegenResult(files=[])

        for plugin in self.plugins:
            files = plugin.generate_code(types, operation)

            result.files.extend(files)

        return result

    def on_start(self) -> None:
        for plugin in self.plugins:
            plugin.on_start()

    def on_end(self, result: CodegenResult) -> None:
        for plugin in self.plugins:
            plugin.on_end(result)


class QueryCodegen:
    def __init__(self, schema: strawberry.Schema, plugins: List[QueryCodegenPlugin]):
        self.schema = schema
        self.plugin_manager = QueryCodegenPluginManager(plugins)
        self.types: List[GraphQLType] = []

    def run(self, query: str) -> CodegenResult:
        self.plugin_manager.on_start()

        ast = parse(query)

        operations = self._get_operations(ast)

        if not operations:
            raise NoOperationProvidedError()

        if len(operations) > 1:
            raise MultipleOperationsProvidedError()

        operation = operations[0]

        if operation.name is None:
            raise NoOperationNameProvidedError()

        self.operation = self._convert_operation(operation)

        result = self.generate_code()
        self.plugin_manager.on_end(result)

        return result

    def _collect_type(self, type_: GraphQLType) -> None:
        if type_ in self.types:
            return

        self.types.append(type_)

    def _convert_selection(self, selection: SelectionNode) -> GraphQLSelection:
        if isinstance(selection, FieldNode):
            return GraphQLFieldSelection(
                selection.name.value,
                selection.alias.value if selection.alias else None,
                selections=self._convert_selection_set(selection.selection_set),
                directives=self._convert_directives(selection.directives),
                arguments=self._convert_arguments(selection.arguments),
            )

        if isinstance(selection, InlineFragmentNode):
            return GraphQLInlineFragment(
                selection.type_condition.name.value,
                self._convert_selection_set(selection.selection_set),
            )

        raise ValueError(f"Unsupported type: {type(selection)}")  # pragma: no cover

    def _convert_selection_set(
        self, selection_set: Optional[SelectionSetNode]
    ) -> List[GraphQLSelection]:

        if selection_set is None:
            return []

        return [
            self._convert_selection(selection) for selection in selection_set.selections
        ]

    def _convert_value(self, value: ValueNode) -> GraphQLArgumentValue:
        if isinstance(value, StringValueNode):
            return GraphQLStringValue(value.value)

        if isinstance(value, IntValueNode):
            return GraphQLIntValue(int(value.value))

        if isinstance(value, VariableNode):
            return GraphQLVariableReference(value.name.value)

        if isinstance(value, ListValueNode):
            return GraphQLListValue(
                [self._convert_value(item) for item in value.values]
            )

        if isinstance(value, EnumValueNode):
            return GraphQLEnumValue(value.value)

        if isinstance(value, BooleanValueNode):
            return GraphQLBoolValue(value.value)

        raise ValueError(f"Unsupported type: {type(value)}")  # pragma: no cover

    def _convert_arguments(
        self, arguments: Iterable[ArgumentNode]
    ) -> List[GraphQLArgument]:
        return [
            GraphQLArgument(argument.name.value, self._convert_value(argument.value))
            for argument in arguments
        ]

    def _convert_directives(
        self, directives: Iterable[DirectiveNode]
    ) -> List[GraphQLDirective]:
        return [
            GraphQLDirective(
                directive.name.value,
                self._convert_arguments(directive.arguments),
            )
            for directive in directives
        ]

    def _convert_operation(
        self, operation_definition: OperationDefinitionNode
    ) -> GraphQLOperation:
        query_type = self.schema.get_type_by_name("Query")
        assert isinstance(query_type, TypeDefinition)

        assert operation_definition.name is not None
        operation_name = operation_definition.name.value
        result_class_name = f"{operation_name}Result"

        operation_type = self._collect_types(
            cast(HasSelectionSet, operation_definition),
            parent_type=query_type,
            class_name=result_class_name,
        )

        operation_kind = cast(
            Literal["query", "mutation", "subscription"],
            operation_definition.operation.value,
        )

        variables, variables_type = self._convert_variable_definitions(
            operation_definition.variable_definitions, operation_name=operation_name
        )

        return GraphQLOperation(
            operation_definition.name.value,
            kind=operation_kind,
            selections=self._convert_selection_set(operation_definition.selection_set),
            directives=self._convert_directives(operation_definition.directives),
            variables=variables,
            type=cast(GraphQLObjectType, operation_type),
            variables_type=variables_type,
        )

    def _convert_variable_definitions(
        self,
        variable_definitions: Optional[Iterable[VariableDefinitionNode]],
        operation_name: str,
    ) -> Tuple[List[GraphQLVariable], Optional[GraphQLObjectType]]:
        if not variable_definitions:
            return [], None

        type_ = GraphQLObjectType(f"{operation_name}Variables", [])

        self._collect_type(type_)

        variables: List[GraphQLVariable] = []

        for variable_definition in variable_definitions:
            variable_type = self._collect_type_from_variable(variable_definition.type)
            variable = GraphQLVariable(
                variable_definition.variable.name.value,
                variable_type,
            )

            type_.fields.append(GraphQLField(variable.name, None, variable_type))

            variables.append(variable)

        return variables, type_

    def _get_operations(self, ast: DocumentNode) -> List[OperationDefinitionNode]:
        return [
            definition
            for definition in ast.definitions
            if isinstance(definition, OperationDefinitionNode)
        ]

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
            field_type = self.schema.schema_converter.scalar_registry[field_type]  # type: ignore  # noqa: E501

        if isinstance(field_type, ScalarWrapper):
            python_type = field_type.wrap
            if hasattr(python_type, "__supertype__"):
                python_type = python_type.__supertype__

            return self._collect_scalar(field_type._scalar_definition, python_type)

        if isinstance(field_type, ScalarDefinition):
            return self._collect_scalar(field_type, None)

        elif isinstance(field_type, EnumDefinition):
            return self._collect_enum(field_type)

        raise ValueError(f"Unsupported type: {field_type}")  # pragma: no cover

    def _collect_type_from_strawberry_type(
        self, strawberry_type: Union[type, StrawberryType]
    ) -> GraphQLType:
        type_: GraphQLType

        if isinstance(strawberry_type, StrawberryOptional):
            return GraphQLOptional(
                self._collect_type_from_strawberry_type(strawberry_type.of_type)
            )

        if isinstance(strawberry_type, StrawberryList):
            return GraphQLOptional(
                self._collect_type_from_strawberry_type(strawberry_type.of_type)
            )

        if hasattr(strawberry_type, "_type_definition"):
            strawberry_type = strawberry_type._type_definition  # type: ignore[union-attr]  # noqa: E501

        if isinstance(strawberry_type, TypeDefinition):
            type_ = GraphQLObjectType(
                strawberry_type.name,
                [],
            )

            for field in strawberry_type.fields:
                field_type = self._collect_type_from_strawberry_type(field.type)
                type_.fields.append(GraphQLField(field.name, None, field_type))

            self._collect_type(type_)
        else:
            type_ = self._get_field_type(strawberry_type)

        return type_

    def _collect_type_from_variable(
        self, variable_type: TypeNode, parent_type: Optional[TypeNode] = None
    ) -> GraphQLType:
        type_: Optional[GraphQLType] = None

        if isinstance(variable_type, ListTypeNode):
            type_ = GraphQLList(
                self._collect_type_from_variable(variable_type.type, variable_type)
            )

        elif isinstance(variable_type, NonNullTypeNode):
            return self._collect_type_from_variable(variable_type.type, variable_type)

        elif isinstance(variable_type, NamedTypeNode):
            strawberry_type = self.schema.get_type_by_name(variable_type.name.value)

            assert strawberry_type

            type_ = self._collect_type_from_strawberry_type(strawberry_type)

        assert type_

        if parent_type is not None and isinstance(parent_type, NonNullTypeNode):
            return type_

        return GraphQLOptional(type_)

    def _field_from_selection(
        self, selection: FieldNode, parent_type: TypeDefinition
    ) -> GraphQLField:
        field = self.schema.get_field_for_type(selection.name.value, parent_type.name)
        assert field

        field_type = self._get_field_type(field.type)

        return GraphQLField(
            field.name, selection.alias.value if selection.alias else None, field_type
        )

    def _unwrap_type(
        self, type_: Union[type, StrawberryType]
    ) -> Tuple[
        Union[type, StrawberryType], Optional[Callable[[GraphQLType], GraphQLType]]
    ]:
        wrapper = None

        if isinstance(type_, StrawberryOptional):
            type_, wrapper = self._unwrap_type(type_.of_type)
            wrapper = (
                GraphQLOptional
                if wrapper is None
                else lambda t: GraphQLOptional(wrapper(t))  # type: ignore[misc]
            )

        elif isinstance(type_, StrawberryList):
            type_, wrapper = self._unwrap_type(type_.of_type)
            wrapper = (
                GraphQLList
                if wrapper is None
                else lambda t: GraphQLList(wrapper(t))  # type: ignore[misc]
            )

        elif isinstance(type_, LazyType):
            return self._unwrap_type(type_.resolve_type())

        return type_, wrapper

    def _field_from_selection_set(
        self, selection: FieldNode, class_name: str, parent_type: TypeDefinition
    ) -> GraphQLField:
        assert selection.selection_set is not None

        selected_field = self.schema.get_field_for_type(
            selection.name.value, parent_type.name
        )
        assert selected_field

        selected_field_type, wrapper = self._unwrap_type(selected_field.type)
        name = capitalize_first(to_camel_case(selection.name.value))
        class_name = f"{class_name}{(name)}"

        field_type: GraphQLType

        if isinstance(selected_field_type, StrawberryUnion):
            field_type = self._collect_types_with_inline_fragments(
                selection, parent_type, class_name
            )
            return GraphQLField(
                selected_field.name,
                selection.alias.value if selection.alias else None,
                field_type,
            )

        parent_type = cast(
            TypeDefinition, selected_field_type._type_definition  # type: ignore
        )

        field_type = self._collect_types(selection, parent_type, class_name)

        if wrapper:
            field_type = wrapper(field_type)

        return GraphQLField(
            selected_field.name,
            selection.alias.value if selection.alias else None,
            field_type,
        )

    def _get_field(
        self, selection: FieldNode, class_name: str, parent_type: TypeDefinition
    ) -> GraphQLField:

        if selection.selection_set:
            return self._field_from_selection_set(selection, class_name, parent_type)

        return self._field_from_selection(selection, parent_type)

    def _collect_types_with_inline_fragments(
        self,
        selection: HasSelectionSet,
        parent_type: TypeDefinition,
        class_name: str,
    ) -> Union[GraphQLObjectType, GraphQLUnion]:
        sub_types = self._collect_types_using_fragments(
            selection, parent_type, class_name
        )

        if len(sub_types) == 1:
            return sub_types[0]

        union = GraphQLUnion(class_name, sub_types)

        self._collect_type(union)

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

        for sub_selection in selection_set.selections:
            assert isinstance(sub_selection, FieldNode)

            field = self._get_field(sub_selection, class_name, parent_type)

            current_type.fields.append(field)

        self._collect_type(current_type)

        return current_type

    def generate_code(self) -> CodegenResult:
        return self.plugin_manager.generate_code(
            types=self.types, operation=self.operation
        )

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

                parent_type = cast(
                    TypeDefinition,
                    self.schema.get_type_by_name(fragment.type_condition.name.value),
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
        self, scalar_definition: ScalarDefinition, python_type: Optional[Type]
    ) -> GraphQLScalar:
        graphql_scalar = GraphQLScalar(scalar_definition.name, python_type=python_type)

        self._collect_type(graphql_scalar)

        return graphql_scalar

    def _collect_enum(self, enum: EnumDefinition) -> GraphQLEnum:
        graphql_enum = GraphQLEnum(
            enum.name,
            [value.name for value in enum.values],
            python_type=enum.wrapped_cls,
        )
        self._collect_type(graphql_enum)
        return graphql_enum

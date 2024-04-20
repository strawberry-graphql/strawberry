from __future__ import annotations

from dataclasses import MISSING, dataclass
from enum import Enum
from functools import cmp_to_key, partial
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    cast,
)
from typing_extensions import Literal, Protocol

import rich
from graphql import (
    BooleanValueNode,
    EnumValueNode,
    FieldNode,
    FloatValueNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    IntValueNode,
    ListTypeNode,
    ListValueNode,
    NamedTypeNode,
    NonNullTypeNode,
    NullValueNode,
    ObjectValueNode,
    OperationDefinitionNode,
    StringValueNode,
    VariableNode,
    parse,
)

from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.type import (
    StrawberryList,
    StrawberryOptional,
    StrawberryType,
    get_object_definition,
    has_object_definition,
)
from strawberry.types.types import StrawberryObjectDefinition
from strawberry.union import StrawberryUnion
from strawberry.unset import UNSET
from strawberry.utils.str_converters import capitalize_first, to_camel_case

from .exceptions import (
    MultipleOperationsProvidedError,
    NoOperationNameProvidedError,
    NoOperationProvidedError,
)
from .types import (
    GraphQLArgument,
    GraphQLBoolValue,
    GraphQLDirective,
    GraphQLEnum,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFieldSelection,
    GraphQLFloatValue,
    GraphQLFragmentSpread,
    GraphQLFragmentType,
    GraphQLInlineFragment,
    GraphQLIntValue,
    GraphQLList,
    GraphQLListValue,
    GraphQLNullValue,
    GraphQLObjectType,
    GraphQLObjectValue,
    GraphQLOperation,
    GraphQLOptional,
    GraphQLScalar,
    GraphQLStringValue,
    GraphQLUnion,
    GraphQLVariable,
    GraphQLVariableReference,
)

if TYPE_CHECKING:
    from graphql import (
        ArgumentNode,
        DirectiveNode,
        DocumentNode,
        SelectionNode,
        SelectionSetNode,
        TypeNode,
        ValueNode,
        VariableDefinitionNode,
    )

    from strawberry.schema import Schema

    from .types import GraphQLArgumentValue, GraphQLSelection, GraphQLType


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
            destination.parent.mkdir(exist_ok=True, parents=True)
            destination.write_text(file.content)


class HasSelectionSet(Protocol):
    selection_set: Optional[SelectionSetNode]


class QueryCodegenPlugin:
    def __init__(self, query: Path) -> None:
        """Initialize the plugin.

        The singular argument is the path to the file that is being processed
        by this plugin.
        """
        self.query = query

    def on_start(self) -> None: ...

    def on_end(self, result: CodegenResult) -> None: ...

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        return []


class ConsolePlugin:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.files_generated: List[Path] = []

    def before_any_start(self) -> None:
        rich.print(
            "[bold yellow]The codegen is experimental. Please submit any bug at "
            "https://github.com/strawberry-graphql/strawberry\n",
        )

    def after_all_finished(self) -> None:
        rich.print("[green]Generated:")
        for fname in self.files_generated:
            rich.print(f"  {fname}")

    def on_start(self, plugins: Iterable[QueryCodegenPlugin], query: Path) -> None:
        plugin_names = [plugin.__class__.__name__ for plugin in plugins]

        rich.print(
            f"[green]Generating code for {query} using "
            f"{', '.join(plugin_names)} plugin(s)",
        )

    def on_end(self, result: CodegenResult) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        result.write(self.output_dir)

        self.files_generated.extend(Path(cf.path) for cf in result.files)

        rich.print(
            f"[green] Generated {len(result.files)} files in {self.output_dir}",
        )


def _get_deps(t: GraphQLType) -> Iterable[GraphQLType]:
    """Get all the types that `t` depends on.

    To keep things simple, `t` depends on itself.
    """
    yield t

    if isinstance(t, GraphQLObjectType):
        for fld in t.fields:
            yield from _get_deps(fld.type)

    elif isinstance(t, (GraphQLEnum, GraphQLScalar)):
        # enums and scalars have no dependent types
        pass

    elif isinstance(t, (GraphQLOptional, GraphQLList)):
        yield from _get_deps(t.of_type)

    elif isinstance(t, GraphQLUnion):
        for gql_type in t.types:
            yield from _get_deps(gql_type)
    else:
        # Want to make sure that all types are covered.
        raise ValueError(f"Unknown GraphQLType: {t}")


_TYPE_TO_GRAPHQL_TYPE = {
    int: GraphQLIntValue,
    float: GraphQLFloatValue,
    str: GraphQLStringValue,
    bool: GraphQLBoolValue,
}


def _py_to_graphql_value(obj: Any) -> GraphQLArgumentValue:
    """Convert a python object to a GraphQLArgumentValue."""
    if obj is None or obj is UNSET:
        return GraphQLNullValue(value=obj)

    obj_type = type(obj)
    if obj_type in _TYPE_TO_GRAPHQL_TYPE:
        return _TYPE_TO_GRAPHQL_TYPE[obj_type](obj)
    if issubclass(obj_type, Enum):
        return GraphQLEnumValue(obj.name, enum_type=obj_type.__name__)
    if issubclass(obj_type, Sequence):
        return GraphQLListValue([_py_to_graphql_value(v) for v in obj])
    if issubclass(obj_type, Mapping):
        return GraphQLObjectValue({k: _py_to_graphql_value(v) for k, v in obj.items()})
    raise ValueError(f"Cannot convet {obj!r} into a GraphQLArgumentValue")


class QueryCodegenPluginManager:
    def __init__(
        self,
        plugins: List[QueryCodegenPlugin],
        console_plugin: Optional[ConsolePlugin] = None,
    ) -> None:
        self.plugins = plugins
        self.console_plugin = console_plugin

    def _sort_types(self, types: List[GraphQLType]) -> List[GraphQLType]:
        """Sort the types.

        t1 < t2 iff t2 has a dependency on t1.
        t1 == t2 iff neither type has a dependency on the other.
        """

        def type_cmp(t1: GraphQLType, t2: GraphQLType) -> int:
            """Compare the types."""
            if t1 is t2:
                return 0

            if t1 in _get_deps(t2):
                return -1
            elif t2 in _get_deps(t1):
                return 1
            else:
                return 0

        return sorted(types, key=cmp_to_key(type_cmp))

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> CodegenResult:
        result = CodegenResult(files=[])

        types = self._sort_types(types)

        for plugin in self.plugins:
            files = plugin.generate_code(types, operation)

            result.files.extend(files)

        return result

    def on_start(self) -> None:
        if self.console_plugin and self.plugins:
            # We need the query that we're processing
            # just pick it off the first plugin
            query = self.plugins[0].query
            self.console_plugin.on_start(self.plugins, query)

        for plugin in self.plugins:
            plugin.on_start()

    def on_end(self, result: CodegenResult) -> None:
        for plugin in self.plugins:
            plugin.on_end(result)

        if self.console_plugin:
            self.console_plugin.on_end(result)


class QueryCodegen:
    def __init__(
        self,
        schema: Schema,
        plugins: List[QueryCodegenPlugin],
        console_plugin: Optional[ConsolePlugin] = None,
    ) -> None:
        self.schema = schema
        self.plugin_manager = QueryCodegenPluginManager(plugins, console_plugin)
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

        # Look for any free-floating fragments and create types out of them
        # These types can then be referenced and included later via the
        # fragment spread operator.
        self._populate_fragment_types(ast)
        self.operation = self._convert_operation(operation)

        result = self.generate_code()
        self.plugin_manager.on_end(result)

        return result

    def _collect_type(self, type_: GraphQLType) -> None:
        if type_ in self.types:
            return

        self.types.append(type_)

    def _populate_fragment_types(self, ast: DocumentNode) -> None:
        fragment_definitions = (
            definition
            for definition in ast.definitions
            if isinstance(definition, FragmentDefinitionNode)
        )
        for fd in fragment_definitions:
            query_type = self.schema.get_type_by_name(fd.type_condition.name.value)
            assert isinstance(
                query_type, StrawberryObjectDefinition
            ), f"{fd.type_condition.name.value!r} is not a type in the graphql schema!"

            typename = fd.type_condition.name.value
            graph_ql_object_type_factory = partial(
                GraphQLFragmentType,
                on=typename,
                graphql_typename=typename,
            )

            self._collect_types(
                # The FragmentDefinitionNode has a non-Optional `SelectionSetNode` but
                # the Protocol wants an `Optional[SelectionSetNode]` so this doesn't
                # quite conform.
                cast(HasSelectionSet, fd),
                parent_type=query_type,
                class_name=fd.name.value,
                graph_ql_object_type_factory=graph_ql_object_type_factory,
            )

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

        if isinstance(selection, FragmentSpreadNode):
            return GraphQLFragmentSpread(selection.name.value)

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

        if isinstance(value, FloatValueNode):
            return GraphQLFloatValue(float(value.value))

        if isinstance(value, NullValueNode):
            return GraphQLNullValue()

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

        if isinstance(value, ObjectValueNode):
            return GraphQLObjectValue(
                {
                    field.name.value: self._convert_value(field.value)
                    for field in value.fields
                }
            )

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
        query_type = self.schema.get_type_by_name(
            operation_definition.operation.value.title()
        )
        assert isinstance(query_type, StrawberryObjectDefinition)

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
            type=cast("GraphQLObjectType", operation_type),
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
            field_type = self.schema.schema_converter.scalar_registry[field_type]  # type: ignore

        if isinstance(field_type, ScalarWrapper):
            python_type = field_type.wrap
            if hasattr(python_type, "__supertype__"):
                python_type = python_type.__supertype__

            return self._collect_scalar(field_type._scalar_definition, python_type)  # type: ignore

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
            return GraphQLList(
                self._collect_type_from_strawberry_type(strawberry_type.of_type)
            )

        if has_object_definition(strawberry_type):
            strawberry_type = strawberry_type.__strawberry_definition__

        if isinstance(strawberry_type, StrawberryObjectDefinition):
            type_ = GraphQLObjectType(
                strawberry_type.name,
                [],
            )

            for field in strawberry_type.fields:
                field_type = self._collect_type_from_strawberry_type(field.type)
                default = None
                if field.default is not MISSING:
                    default = _py_to_graphql_value(field.default)
                type_.fields.append(
                    GraphQLField(field.name, None, field_type, default_value=default)
                )

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
        self, selection: FieldNode, parent_type: StrawberryObjectDefinition
    ) -> GraphQLField:
        if selection.name.value == "__typename":
            return GraphQLField("__typename", None, GraphQLScalar("String", None))
        field = self.schema.get_field_for_type(selection.name.value, parent_type.name)
        assert field, f"{parent_type.name},{selection.name.value}"

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
                GraphQLList if wrapper is None else lambda t: GraphQLList(wrapper(t))
            )

        elif isinstance(type_, LazyType):
            return self._unwrap_type(type_.resolve_type())

        return type_, wrapper

    def _field_from_selection_set(
        self,
        selection: FieldNode,
        class_name: str,
        parent_type: StrawberryObjectDefinition,
    ) -> GraphQLField:
        assert selection.selection_set is not None

        parent_type_name = parent_type.name

        # Check if the parent type is generic.
        # This seems to be tracked by `strawberry` in the `type_var_map`
        # If the type is generic, then the strawberry generated schema
        # naming convention is <GenericType,...><ClassName>
        # The implementation here assumes that the `type_var_map` is ordered,
        # but insertion order is maintained in python3.6+ (for CPython) and
        # guaranteed for all python implementations in python3.7+, so that
        # should be pretty safe.
        if parent_type.type_var_map:
            parent_type_name = (
                "".join(
                    c.__name__  # type: ignore[union-attr]
                    for c in parent_type.type_var_map.values()
                )
                + parent_type.name
            )

        selected_field = self.schema.get_field_for_type(
            selection.name.value, parent_type_name
        )

        assert (
            selected_field
        ), f"Couldn't find {parent_type_name}.{selection.name.value}"

        selected_field_type, wrapper = self._unwrap_type(selected_field.type)
        name = capitalize_first(to_camel_case(selection.name.value))
        class_name = f"{class_name}{(name)}"

        field_type: GraphQLType

        if isinstance(selected_field_type, StrawberryUnion):
            field_type = self._collect_types_with_inline_fragments(
                selection, parent_type, class_name
            )
        else:
            parent_type = get_object_definition(selected_field_type, strict=True)
            field_type = self._collect_types(selection, parent_type, class_name)

        if wrapper:
            field_type = wrapper(field_type)

        return GraphQLField(
            selected_field.name,
            selection.alias.value if selection.alias else None,
            field_type,
        )

    def _get_field(
        self,
        selection: FieldNode,
        class_name: str,
        parent_type: StrawberryObjectDefinition,
    ) -> GraphQLField:
        if selection.selection_set:
            return self._field_from_selection_set(selection, class_name, parent_type)

        return self._field_from_selection(selection, parent_type)

    def _collect_types_with_inline_fragments(
        self,
        selection: HasSelectionSet,
        parent_type: StrawberryObjectDefinition,
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
        parent_type: StrawberryObjectDefinition,
        class_name: str,
        graph_ql_object_type_factory: Callable[
            [str], GraphQLObjectType
        ] = GraphQLObjectType,
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

        current_type = graph_ql_object_type_factory(class_name)
        fields: List[Union[GraphQLFragmentSpread, GraphQLField]] = []

        for sub_selection in selection_set.selections:
            if isinstance(sub_selection, FragmentSpreadNode):
                fields.append(GraphQLFragmentSpread(sub_selection.name.value))
                continue
            assert isinstance(sub_selection, FieldNode)
            field = self._get_field(sub_selection, class_name, parent_type)

            fields.append(field)

        if any(isinstance(f, GraphQLFragmentSpread) for f in fields):
            if len(fields) > 1:
                raise ValueError(
                    "Queries with Fragments cannot currently include separate fields."
                )
            spread_field = fields[0]
            assert isinstance(spread_field, GraphQLFragmentSpread)
            return next(
                t
                for t in self.types
                if isinstance(t, GraphQLObjectType) and t.name == spread_field.name
            )

        # This cast is safe because all the fields are either
        # `GraphQLField` or `GraphQLFragmentSpread`
        # and the suite above will cause this statement to be
        # skipped if there are any `GraphQLFragmentSpread`.
        current_type.fields = cast(List[GraphQLField], fields)

        self._collect_type(current_type)

        return current_type

    def generate_code(self) -> CodegenResult:
        return self.plugin_manager.generate_code(
            types=self.types, operation=self.operation
        )

    def _collect_types_using_fragments(
        self,
        selection: HasSelectionSet,
        parent_type: StrawberryObjectDefinition,
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

        all_common_fields_typename = all(f.name == "__typename" for f in common_fields)

        for fragment in fragments:
            type_condition_name = fragment.type_condition.name.value
            fragment_class_name = class_name + type_condition_name

            current_type = GraphQLObjectType(
                fragment_class_name,
                list(common_fields),
                graphql_typename=type_condition_name,
            )
            fields: List[Union[GraphQLFragmentSpread, GraphQLField]] = []

            for sub_selection in fragment.selection_set.selections:
                if isinstance(sub_selection, FragmentSpreadNode):
                    fields.append(GraphQLFragmentSpread(sub_selection.name.value))
                    continue

                assert isinstance(sub_selection, FieldNode)

                parent_type = cast(
                    StrawberryObjectDefinition,
                    self.schema.get_type_by_name(type_condition_name),
                )

                assert parent_type, type_condition_name

                fields.append(
                    self._get_field(
                        selection=sub_selection,
                        class_name=fragment_class_name,
                        parent_type=parent_type,
                    )
                )

            if any(isinstance(f, GraphQLFragmentSpread) for f in fields):
                if len(fields) > 1:
                    raise ValueError(
                        "Queries with Fragments cannot include separate fields."
                    )
                spread_field = fields[0]
                assert isinstance(spread_field, GraphQLFragmentSpread)
                sub_type = next(
                    t
                    for t in self.types
                    if isinstance(t, GraphQLObjectType) and t.name == spread_field.name
                )
                fields = [*sub_type.fields]
                if all_common_fields_typename:  # No need to create a new type.
                    sub_types.append(sub_type)
                    continue

            # This cast is safe because all the fields are either
            # `GraphQLField` or `GraphQLFragmentSpread`
            # and the suite above will cause this statement to be
            # skipped if there are any `GraphQLFragmentSpread`.
            current_type.fields.extend(cast(List[GraphQLField], fields))

            sub_types.append(current_type)

        for sub_type in sub_types:
            self._collect_type(sub_type)

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

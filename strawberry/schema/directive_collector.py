from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from graphql import (
    get_named_type,
    is_enum_type,
    is_input_object_type,
    is_interface_type,
    is_object_type,
    is_scalar_type,
    is_union_type,
)

from strawberry.exceptions import (
    DuplicateSchemaDirectiveError,
    InvalidSchemaDirectiveLocationError,
)
from strawberry.schema_directive import Location, StrawberrySchemaDirective

from .compat import is_schema_directive
from .schema_converter import GraphQLCoreConverter

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from graphql import GraphQLDirective, GraphQLNamedType, GraphQLType


class SchemaDirectiveCollector:
    """Discovers the schema directives attached to Strawberry definitions.

    graphql-core adds the argument types of every directive passed to
    ``GraphQLSchema`` to its type map, but it cannot discover directives that
    are stored only on Strawberry definitions. This collector walks the same
    GraphQL types graphql-core will reach, records every attached directive,
    converts each directive class once, and queues the converted directive's
    argument types so directives attached inside nested directive-only input
    types are found as well.
    """

    def __init__(self, converter: GraphQLCoreConverter) -> None:
        self._converter = converter

        # Directive classes in discovery order. A plain subclass inherits its
        # parent's definition, so it is another Python spelling of the same
        # GraphQL directive and is recorded as an alias instead.
        self.directive_types: list[type] = []
        self.graphql_directives: dict[type, GraphQLDirective] = {}
        self._seen_directive_types: set[type] = set()
        self._types_by_definition: dict[int, type] = {}
        self._aliases: dict[type, type] = {}

        # Every application found on a type, field, argument or enum value, in
        # traversal order. Federation derives @link and @composeDirective from
        # these, so the order is kept independent of the definitions above.
        self.directives_in_use: list[object] = []
        self._schema_directive_definitions: dict[str, StrawberrySchemaDirective] = {}

        self._graphql_types: list[GraphQLNamedType] = []
        self._seen_graphql_types: set[int] = set()
        self._type_cursor = 0
        self._directive_cursor = 0

    def add_directive_type(self, directive_type: type) -> None:
        if directive_type in self._seen_directive_types:
            return

        self._seen_directive_types.add(directive_type)
        definition = cast("Any", directive_type).__strawberry_directive__
        canonical_type = self._types_by_definition.setdefault(
            id(definition), directive_type
        )
        if canonical_type is not directive_type:
            self._aliases[directive_type] = canonical_type
            return

        self.directive_types.append(directive_type)

    def add_schema_directives(self, directives: Iterable[object]) -> None:
        """Register directives applied to the schema definition itself."""
        self._record_directives(
            directives,
            location=Location.SCHEMA,
            element="schema",
            seen_directives=self._schema_directive_definitions,
            record_in_use=False,
        )

    def add_graphql_types(self, graphql_types: Iterable[GraphQLType | None]) -> None:
        for graphql_type in graphql_types:
            if graphql_type is not None:
                self._queue_graphql_type(graphql_type)

    def collect(self) -> None:
        """Process queued types and directives until nothing new is found."""
        while self._type_cursor < len(self._graphql_types) or (
            self._directive_cursor < len(self.directive_types)
        ):
            while self._type_cursor < len(self._graphql_types):
                graphql_type = self._graphql_types[self._type_cursor]
                self._type_cursor += 1
                self._visit_graphql_type(graphql_type)

            # Conversion exposes argument input types that graphql-core can only
            # contribute once the directive is registered. Queue them so any
            # directives attached inside that input graph are discovered too.
            while self._directive_cursor < len(self.directive_types):
                directive_type = self.directive_types[self._directive_cursor]
                self._directive_cursor += 1
                graphql_directive = self._converter.from_schema_directive(
                    directive_type
                )
                self.graphql_directives[directive_type] = graphql_directive
                for argument in graphql_directive.args.values():
                    self._queue_graphql_type(argument.type)

        for alias, canonical_type in self._aliases.items():
            self.graphql_directives[alias] = self.graphql_directives[canonical_type]

    def _record_directives(
        self,
        directives: Iterable[object],
        *,
        location: Location,
        element: str,
        source: type | Callable[..., Any] | None = None,
        source_attribute: str | None = None,
        source_argument: str | None = None,
        seen_directives: dict[str, StrawberrySchemaDirective] | None = None,
        record_in_use: bool = True,
    ) -> None:
        seen_directives = seen_directives if seen_directives is not None else {}

        for directive in directives:
            if record_in_use:
                self.directives_in_use.append(directive)

            directive_type = directive.__class__
            if not is_schema_directive(directive_type):
                continue

            definition = cast(
                "StrawberrySchemaDirective",
                cast("Any", directive_type).__strawberry_directive__,
            )
            directive_name = self._converter.config.name_converter.from_directive(
                definition
            )

            if location not in definition.locations:
                raise InvalidSchemaDirectiveLocationError(
                    directive_name,
                    location,
                    element,
                    definition.locations,
                    source=source,
                    source_attribute=source_attribute,
                    source_argument=source_argument,
                )

            if (previous := seen_directives.get(directive_name)) is not None and (
                not previous.repeatable or not definition.repeatable
            ):
                raise DuplicateSchemaDirectiveError(
                    directive_name,
                    location,
                    element,
                    source=source,
                    source_attribute=source_attribute,
                    source_argument=source_argument,
                )

            seen_directives.setdefault(directive_name, definition)
            self.add_directive_type(directive_type)

    def _record_applied_directives(
        self,
        owner: object,
        *,
        location: Location,
        element: str,
        source: type | Callable[..., Any] | None = None,
        source_attribute: str | None = None,
        source_argument: str | None = None,
    ) -> None:
        self._record_directives(
            getattr(owner, "directives", None) or (),
            location=location,
            element=element,
            source=source,
            source_attribute=source_attribute,
            source_argument=source_argument,
        )

    def _queue_graphql_type(self, graphql_type: GraphQLType) -> None:
        named_type = get_named_type(graphql_type)
        if id(named_type) in self._seen_graphql_types:
            return

        self._seen_graphql_types.add(id(named_type))
        self._graphql_types.append(named_type)

    @staticmethod
    def _get_type_location(graphql_type: GraphQLNamedType) -> Location | None:
        if is_scalar_type(graphql_type):
            return Location.SCALAR
        if is_object_type(graphql_type):
            return Location.OBJECT
        if is_interface_type(graphql_type):
            return Location.INTERFACE
        if is_union_type(graphql_type):
            return Location.UNION
        if is_enum_type(graphql_type):
            return Location.ENUM
        if is_input_object_type(graphql_type):
            return Location.INPUT_OBJECT

        return None

    def _visit_graphql_type(self, graphql_type: GraphQLNamedType) -> None:
        # Resolve graphql-core's lazy thunks before reading the Strawberry
        # definition. Field extensions can attach schema directives while fields
        # are converted (permissions do this), so inspecting the definition
        # first would miss them.
        graphql_fields = getattr(graphql_type, "fields", {})
        interfaces = getattr(graphql_type, "interfaces", ())
        member_types = getattr(graphql_type, "types", ())

        definition = graphql_type.extensions.get(
            GraphQLCoreConverter.DEFINITION_BACKREF
        )
        if definition is not None:
            location = self._get_type_location(graphql_type)
            source = getattr(definition, "origin", None)
            source = source if isinstance(source, type) else None

            if location is not None:
                self._record_applied_directives(
                    definition,
                    location=location,
                    element=graphql_type.name,
                    source=source,
                )

            field_location = (
                Location.INPUT_FIELD_DEFINITION
                if is_input_object_type(graphql_type)
                else Location.FIELD_DEFINITION
            )
            for field_name, graphql_field in graphql_fields.items():
                field = graphql_field.extensions.get(
                    GraphQLCoreConverter.DEFINITION_BACKREF
                )
                if field is None:
                    continue

                field_source = getattr(field, "origin", None)
                field_source = field_source if isinstance(field_source, type) else None
                field_element = f"{graphql_type.name}.{field_name}"
                self._record_applied_directives(
                    field,
                    location=field_location,
                    element=field_element,
                    source=field_source,
                    source_attribute=getattr(field, "python_name", None),
                )

                resolver = getattr(field, "base_resolver", None)
                resolver_source = getattr(resolver, "wrapped_func", None)
                for argument_name, graphql_argument in getattr(
                    graphql_field, "args", {}
                ).items():
                    argument = graphql_argument.extensions.get(
                        GraphQLCoreConverter.DEFINITION_BACKREF
                    )
                    if argument is None:
                        continue

                    self._record_applied_directives(
                        argument,
                        location=Location.ARGUMENT_DEFINITION,
                        element=f"{field_element}({argument_name}:)",
                        source=resolver_source,
                        source_argument=getattr(argument, "python_name", None),
                    )

            for value_name, graphql_value in getattr(
                graphql_type, "values", {}
            ).items():
                value = graphql_value.extensions.get(
                    GraphQLCoreConverter.DEFINITION_BACKREF
                )
                if value is not None:
                    self._record_applied_directives(
                        value,
                        location=Location.ENUM_VALUE,
                        element=f"{graphql_type.name}.{value_name}",
                        source=source,
                    )

        for field in graphql_fields.values():
            self._queue_graphql_type(field.type)
            for argument in getattr(field, "args", {}).values():
                self._queue_graphql_type(argument.type)
        for interface in interfaces:
            self._queue_graphql_type(interface)
        for member_type in member_types:
            self._queue_graphql_type(member_type)


__all__ = ["SchemaDirectiveCollector"]

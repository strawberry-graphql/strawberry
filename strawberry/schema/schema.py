from __future__ import annotations

import warnings
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
    cast,
)

from graphql import (
    GraphQLBoolean,
    GraphQLField,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLSchema,
    get_introspection_query,
    parse,
    validate_schema,
)
from graphql.execution import subscribe
from graphql.type.directives import specified_directives

from strawberry import relay
from strawberry.annotation import StrawberryAnnotation
from strawberry.extensions.directives import (
    DirectivesExtension,
    DirectivesExtensionSync,
)
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types import ExecutionContext
from strawberry.types.base import StrawberryObjectDefinition, has_object_definition
from strawberry.types.graphql import OperationType

from ..printer import print_schema
from ..utils.await_maybe import await_maybe
from . import compat
from .base import BaseSchema
from .config import StrawberryConfig
from .execute import execute, execute_sync

if TYPE_CHECKING:
    from graphql import ExecutionContext as GraphQLExecutionContext
    from graphql import ExecutionResult as GraphQLExecutionResult

    from strawberry.directive import StrawberryDirective
    from strawberry.extensions import SchemaExtension
    from strawberry.types import ExecutionResult
    from strawberry.types.base import StrawberryType
    from strawberry.types.enum import EnumDefinition
    from strawberry.types.field import StrawberryField
    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper
    from strawberry.types.union import StrawberryUnion

DEFAULT_ALLOWED_OPERATION_TYPES = {
    OperationType.QUERY,
    OperationType.MUTATION,
    OperationType.SUBSCRIPTION,
}


class Schema(BaseSchema):
    def __init__(
        self,
        # TODO: can we make sure we only allow to pass
        # something that has been decorated?
        query: Type,
        mutation: Optional[Type] = None,
        subscription: Optional[Type] = None,
        directives: Iterable[StrawberryDirective] = (),
        types: Iterable[Union[Type, StrawberryType]] = (),
        extensions: Iterable[Union[Type[SchemaExtension], SchemaExtension]] = (),
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
        config: Optional[StrawberryConfig] = None,
        scalar_overrides: Optional[
            Dict[object, Union[Type, ScalarWrapper, ScalarDefinition]],
        ] = None,
        schema_directives: Iterable[object] = (),
    ) -> None:
        """Default Schema to be to be used in a Strawberry application.

        A GraphQL Schema class used to define the structure and configuration
        of GraphQL queries, mutations, and subscriptions.

        This class allows the creation of a GraphQL schema by specifying the types
        for queries, mutations, and subscriptions, along with various configuration
        options such as directives, extensions, and scalar overrides.

        Args:
            query: The entry point for queries.
            mutation: The entry point for mutations.
            subscription: The entry point for subscriptions.
            directives: A list of operation directives that clients can use.
                The bult-in `@include` and `@skip` are included by default.
            types: A list of additional types that will be included in the schema.
            extensions: A list of Strawberry extensions.
            execution_context_class: The execution context class.
            config: The configuration for the schema.
            scalar_overrides: A dictionary of overrides for scalars.
            schema_directives: A list of schema directives for the schema.

        Example:
        ```python
        import strawberry


        @strawberry.type
        class Query:
            name: str = "Patrick"


        schema = strawberry.Schema(query=Query)
        ```
        """
        self.query = query
        self.mutation = mutation
        self.subscription = subscription

        self.extensions = extensions
        self.execution_context_class = execution_context_class
        self.config = config or StrawberryConfig()

        SCALAR_OVERRIDES_DICT_TYPE = Dict[
            object, Union["ScalarWrapper", "ScalarDefinition"]
        ]

        scalar_registry: SCALAR_OVERRIDES_DICT_TYPE = {**DEFAULT_SCALAR_REGISTRY}
        if scalar_overrides:
            # TODO: check that the overrides are valid
            scalar_registry.update(cast(SCALAR_OVERRIDES_DICT_TYPE, scalar_overrides))

        self.schema_converter = GraphQLCoreConverter(
            self.config, scalar_registry, self.get_fields
        )
        self.directives = directives
        self.schema_directives = list(schema_directives)

        query_type = self.schema_converter.from_object(query.__strawberry_definition__)
        mutation_type = (
            self.schema_converter.from_object(mutation.__strawberry_definition__)
            if mutation
            else None
        )
        subscription_type = (
            self.schema_converter.from_object(subscription.__strawberry_definition__)
            if subscription
            else None
        )

        graphql_directives = [
            self.schema_converter.from_directive(directive) for directive in directives
        ]

        graphql_types = []
        for type_ in types:
            if compat.is_schema_directive(type_):
                graphql_directives.append(
                    self.schema_converter.from_schema_directive(type_)
                )
            else:
                if has_object_definition(type_):
                    if type_.__strawberry_definition__.is_graphql_generic:
                        type_ = StrawberryAnnotation(type_).resolve()  # noqa: PLW2901
                graphql_type = self.schema_converter.from_maybe_optional(type_)
                if isinstance(graphql_type, GraphQLNonNull):
                    graphql_type = graphql_type.of_type
                if not isinstance(graphql_type, GraphQLNamedType):
                    raise TypeError(f"{graphql_type} is not a named GraphQL Type")
                graphql_types.append(graphql_type)

        try:
            self._schema = GraphQLSchema(
                query=query_type,
                mutation=mutation_type,
                subscription=subscription_type if subscription else None,
                directives=specified_directives + tuple(graphql_directives),
                types=graphql_types,
                extensions={
                    GraphQLCoreConverter.DEFINITION_BACKREF: self,
                },
            )

        except TypeError as error:
            # GraphQL core throws a TypeError if there's any exception raised
            # during the schema creation, so we check if the cause was a
            # StrawberryError and raise it instead if that's the case.

            from strawberry.exceptions import StrawberryException

            if isinstance(error.__cause__, StrawberryException):
                raise error.__cause__ from None

            raise

        # attach our schema to the GraphQL schema instance
        self._schema._strawberry_schema = self  # type: ignore

        self._warn_for_federation_directives()
        self._resolve_node_ids()
        self._extend_introspection()

        # Validate schema early because we want developers to know about
        # possible issues as soon as possible
        errors = validate_schema(self._schema)
        if errors:
            formatted_errors = "\n\n".join(f"❌ {error.message}" for error in errors)
            raise ValueError(f"Invalid Schema. Errors:\n\n{formatted_errors}")

    def get_extensions(
        self, sync: bool = False
    ) -> List[Union[Type[SchemaExtension], SchemaExtension]]:
        extensions = list(self.extensions)

        if self.directives:
            extensions.append(DirectivesExtensionSync if sync else DirectivesExtension)

        return extensions

    @lru_cache
    def get_type_by_name(
        self, name: str
    ) -> Optional[
        Union[
            StrawberryObjectDefinition,
            ScalarDefinition,
            EnumDefinition,
            StrawberryUnion,
        ]
    ]:
        # TODO: respect auto_camel_case
        if name in self.schema_converter.type_map:
            return self.schema_converter.type_map[name].definition

        return None

    def get_field_for_type(
        self, field_name: str, type_name: str
    ) -> Optional[StrawberryField]:
        type_ = self.get_type_by_name(type_name)

        if not type_:
            return None  # pragma: no cover

        assert isinstance(type_, StrawberryObjectDefinition)

        return next(
            (
                field
                for field in type_.fields
                if self.config.name_converter.get_graphql_name(field) == field_name
            ),
            None,
        )

    @lru_cache
    def get_directive_by_name(self, graphql_name: str) -> Optional[StrawberryDirective]:
        return next(
            (
                directive
                for directive in self.directives
                if self.config.name_converter.from_directive(directive) == graphql_name
            ),
            None,
        )

    def get_fields(
        self, type_definition: StrawberryObjectDefinition
    ) -> List[StrawberryField]:
        return type_definition.fields

    async def execute(
        self,
        query: Optional[str],
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
    ) -> ExecutionResult:
        if allowed_operation_types is None:
            allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES

        # Create execution context
        execution_context = ExecutionContext(
            query=query,
            schema=self,
            context=context_value,
            root_value=root_value,
            variables=variable_values,
            provided_operation_name=operation_name,
        )

        result = await execute(
            self._schema,
            extensions=self.get_extensions(),
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
            allowed_operation_types=allowed_operation_types,
            process_errors=self._process_errors,
        )

        return result

    def execute_sync(
        self,
        query: Optional[str],
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
        allowed_operation_types: Optional[Iterable[OperationType]] = None,
    ) -> ExecutionResult:
        if allowed_operation_types is None:
            allowed_operation_types = DEFAULT_ALLOWED_OPERATION_TYPES

        execution_context = ExecutionContext(
            query=query,
            schema=self,
            context=context_value,
            root_value=root_value,
            variables=variable_values,
            provided_operation_name=operation_name,
        )

        result = execute_sync(
            self._schema,
            extensions=self.get_extensions(sync=True),
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
            allowed_operation_types=allowed_operation_types,
            process_errors=self._process_errors,
        )

        return result

    async def subscribe(
        self,
        # TODO: make this optional when we support extensions
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ) -> Union[AsyncIterator[GraphQLExecutionResult], GraphQLExecutionResult]:
        return await await_maybe(
            subscribe(
                self._schema,
                parse(query),
                root_value=root_value,
                context_value=context_value,
                variable_values=variable_values,
                operation_name=operation_name,
            )
        )

    def _resolve_node_ids(self) -> None:
        for concrete_type in self.schema_converter.type_map.values():
            type_def = concrete_type.definition

            # This can be a TypeDefinition, EnumDefinition, ScalarDefinition
            # or UnionDefinition
            if not isinstance(type_def, StrawberryObjectDefinition):
                continue

            # Do not validate id_attr for interfaces. relay.Node itself and
            # any other interfdace that implements it are not required to
            # provide a NodeID annotation, only the concrete type implementing
            # them needs to do that.
            if type_def.is_interface:
                continue

            # Call resolve_id_attr in here to make sure we raise provide
            # early feedback for missing NodeID annotations
            origin = type_def.origin
            if issubclass(origin, relay.Node):
                has_custom_resolve_id = False
                for base in origin.__mro__:
                    if base is relay.Node:
                        break
                    if "resolve_id" in base.__dict__:
                        has_custom_resolve_id = True
                        break

                if not has_custom_resolve_id:
                    origin.resolve_id_attr()

    def _warn_for_federation_directives(self) -> None:
        """Raises a warning if the schema has any federation directives."""
        from strawberry.federation.schema_directives import FederationDirective

        all_types = self.schema_converter.type_map.values()
        all_type_defs = (type_.definition for type_ in all_types)

        all_directives = (
            directive
            for type_def in all_type_defs
            for directive in (type_def.directives or [])
        )

        if any(
            isinstance(directive, FederationDirective) for directive in all_directives
        ):
            warnings.warn(
                "Federation directive found in schema. "
                "Use `strawberry.federation.Schema` instead of `strawberry.Schema`.",
                UserWarning,
                stacklevel=3,
            )

    def _extend_introspection(self) -> None:
        def _resolve_is_one_of(obj: Any, info: Any) -> bool:
            if "strawberry-definition" not in obj.extensions:
                return False

            return obj.extensions["strawberry-definition"].is_one_of

        instrospection_type = self._schema.type_map["__Type"]
        instrospection_type.fields["isOneOf"] = GraphQLField(GraphQLBoolean)  # type: ignore[attr-defined]
        instrospection_type.fields["isOneOf"].resolve = _resolve_is_one_of  # type: ignore[attr-defined]

    def as_str(self) -> str:
        return print_schema(self)

    __str__ = as_str

    def introspect(self) -> Dict[str, Any]:
        """Return the introspection query result for the current schema.

        Raises:
            ValueError: If the introspection query fails due to an invalid schema
        """
        introspection = self.execute_sync(get_introspection_query())
        if introspection.errors or not introspection.data:
            raise ValueError(f"Invalid Schema. Errors {introspection.errors!r}")

        return introspection.data


__all__ = ["Schema"]

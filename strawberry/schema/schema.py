from functools import lru_cache
from typing import Any, Dict, Iterable, Optional, Sequence, Type, Union

from graphql import (
    ExecutionContext as GraphQLExecutionContext,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLSchema,
    get_introspection_query,
    parse,
    validate_schema,
)
from graphql.subscription import subscribe
from graphql.type.directives import specified_directives

from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.directive import StrawberryDirective
from strawberry.enum import EnumDefinition
from strawberry.extensions import Extension
from strawberry.extensions.directives import (
    DirectivesExtension,
    DirectivesExtensionSync,
)
from strawberry.field import StrawberryField
from strawberry.schema.schema_converter import GraphQLCoreConverter
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types import ExecutionContext, ExecutionResult
from strawberry.types.graphql import OperationType
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion

from ..printer import print_schema
from .base import BaseSchema
from .config import StrawberryConfig
from .execute import execute, execute_sync


DEFAULT_ALLOWED_OPERATION_TYPES = {
    OperationType.QUERY,
    OperationType.MUTATION,
    OperationType.SUBSCRIPTION,
}


class Schema(BaseSchema):
    def __init__(
        self,
        # TODO: can we make sure we only allow to pass something that has been decorated?
        query: Type,
        mutation: Optional[Type] = None,
        subscription: Optional[Type] = None,
        directives: Sequence[StrawberryDirective] = (),
        types=(),
        extensions: Sequence[Union[Type[Extension], Extension]] = (),
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
        config: Optional[StrawberryConfig] = None,
        scalar_overrides: Optional[
            Dict[object, Union[ScalarWrapper, ScalarDefinition]]
        ] = None,
    ):
        self.extensions = extensions
        self.execution_context_class = execution_context_class
        self.config = config or StrawberryConfig()

        scalar_registry: Dict[object, Union[ScalarWrapper, ScalarDefinition]] = {
            **DEFAULT_SCALAR_REGISTRY
        }
        if scalar_overrides:
            scalar_registry.update(scalar_overrides)

        self.schema_converter = GraphQLCoreConverter(self.config, scalar_registry)
        self.directives = directives

        query_type = self.schema_converter.from_object(query._type_definition)
        mutation_type = (
            self.schema_converter.from_object(mutation._type_definition)
            if mutation
            else None
        )
        subscription_type = (
            self.schema_converter.from_object(subscription._type_definition)
            if subscription
            else None
        )

        graphql_directives = tuple(
            self.schema_converter.from_directive(directive) for directive in directives
        )

        graphql_types = []
        for type_ in types:
            graphql_type = self.schema_converter.from_maybe_optional(type_)
            if isinstance(graphql_type, GraphQLNonNull):
                graphql_type = graphql_type.of_type
            if not isinstance(graphql_type, GraphQLNamedType):
                raise TypeError(f"{graphql_type} is not a named GraphQL Type")
            graphql_types.append(graphql_type)

        self._schema = GraphQLSchema(
            query=query_type,
            mutation=mutation_type,
            subscription=subscription_type if subscription else None,
            directives=specified_directives + graphql_directives,
            types=graphql_types,
        )

        # attach our schema to the GraphQL schema instance
        self._schema._strawberry_schema = self  # type: ignore

        # Validate schema early because we want developers to know about
        # possible issues as soon as possible
        errors = validate_schema(self._schema)
        if errors:
            formatted_errors = "\n\n".join(f"❌ {error.message}" for error in errors)
            raise ValueError(f"Invalid Schema. Errors:\n\n{formatted_errors}")

        self.query = self.schema_converter.type_map[query_type.name]

    @lru_cache()
    def get_type_by_name(  # type: ignore  # lru_cache makes mypy complain
        self, name: str
    ) -> Optional[
        Union[TypeDefinition, ScalarDefinition, EnumDefinition, StrawberryUnion]
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

        assert isinstance(type_, TypeDefinition)

        return next(
            (
                field
                for field in type_.fields
                if self.config.name_converter.get_graphql_name(field) == field_name
            ),
            None,
        )

    @lru_cache()
    def get_directive_by_name(self, graphql_name: str) -> Optional[StrawberryDirective]:
        return next(
            (
                directive
                for directive in self.directives
                if self.config.name_converter.from_directive(directive) == graphql_name
            ),
            None,
        )

    async def execute(
        self,
        query: str,
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
            query,
            extensions=list(self.extensions) + [DirectivesExtension],
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
            allowed_operation_types=allowed_operation_types,
        )

        if result.errors:
            self.process_errors(result.errors, execution_context=execution_context)

        return result

    def execute_sync(
        self,
        query: str,
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
            query,
            extensions=list(self.extensions) + [DirectivesExtensionSync],
            execution_context_class=self.execution_context_class,
            execution_context=execution_context,
            allowed_operation_types=allowed_operation_types,
        )

        if result.errors:
            self.process_errors(result.errors, execution_context=execution_context)

        return result

    async def subscribe(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ):
        return await subscribe(
            self._schema,
            parse(query),
            root_value=root_value,
            context_value=context_value,
            variable_values=variable_values,
            operation_name=operation_name,
        )

    def as_str(self) -> str:
        return print_schema(self)

    __str__ = as_str

    def introspect(self) -> Dict[str, Any]:
        """Return the introspection query result for the current schema

        Raises:
            ValueError: If the introspection query fails due to an invalid schema
        """
        introspection = self.execute_sync(get_introspection_query())
        if introspection.errors or not introspection.data:
            raise ValueError(f"Invalid Schema. Errors {introspection.errors!r}")

        return introspection.data

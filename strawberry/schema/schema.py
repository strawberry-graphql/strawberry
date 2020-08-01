from typing import Any, Dict, List, Optional, Type, Union

from graphql import GraphQLSchema, graphql_sync, parse
from graphql.subscription import subscribe
from graphql.type.definition import GraphQLType
from graphql.type.directives import specified_directives
from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition
from strawberry.types.types import TypeDefinition

# TODO: get rid of this module ?
from ..graphql import execute
from ..middleware import DirectivesMiddleware, Middleware
from ..printer import print_schema
from .types import ConcreteType, get_directive_type, get_object_type


class Schema:
    def __init__(
        self,
        # TODO: can we make sure we only allow to pass something that has been decorated?
        query: Type,
        mutation: Optional[Type] = None,
        subscription: Optional[Type] = None,
        directives=(),
        types=(),
    ):
        self.type_map: Dict[str, ConcreteType] = {}

        query_type = get_object_type(query, self.type_map)
        mutation_type = get_object_type(mutation, self.type_map) if mutation else None
        subscription_type = (
            get_object_type(subscription, self.type_map) if subscription else None
        )

        self.middleware: List[Middleware] = [DirectivesMiddleware(directives)]

        directives = [
            get_directive_type(directive, self.type_map) for directive in directives
        ]

        types = [get_object_type(type, self.type_map) for type in types]

        self._schema = GraphQLSchema(
            query=query_type,
            mutation=mutation_type,
            subscription=subscription_type if subscription else None,
            directives=specified_directives + directives,
            types=types,
        )

        # TODO: don't use GraphQL core's feature here, let's find the interfaces
        # and types by navigating our schema, so this won't break with changes of
        # GraphQL core, and hopefully the code is cleaner as well.

        types_from_interfaces = self.find_types_from_interfaces()

        for type in types_from_interfaces:
            name = type.name  # type: ignore
            self._schema.type_map[name] = type  # type: ignore

        self.query = self.type_map[query_type.name]

    def find_types_from_interfaces(self) -> List[GraphQLType]:
        types: List[GraphQLType] = []

        collected_types = list(self.type_map.values())

        for type in collected_types:
            if not getattr(type.definition, "is_interface", False):
                continue

            for subclass in type.definition.origin.__subclasses__():  # type: ignore
                types.append(get_object_type(subclass, self.type_map))

        return types

    def get_type_by_name(
        self, name: str
    ) -> Optional[Union[TypeDefinition, ScalarDefinition, EnumDefinition]]:
        if name in self.type_map:
            return self.type_map[name].definition

        return None

    # TODO: type return value of these

    async def execute(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ):
        return await execute(
            self._schema,
            query,
            variable_values=variable_values,
            root_value=root_value,
            context_value=context_value,
            middleware=self.middleware,
            operation_name=operation_name,
        )

    def execute_sync(
        self,
        query: str,
        variable_values: Optional[Dict[str, Any]] = None,
        context_value: Optional[Any] = None,
        root_value: Optional[Any] = None,
        operation_name: Optional[str] = None,
    ):
        return graphql_sync(
            self._schema,
            query,
            variable_values=variable_values,
            root_value=root_value,
            context_value=context_value,
            middleware=self.middleware,
            operation_name=operation_name,
        )

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

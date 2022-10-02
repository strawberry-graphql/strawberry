from collections import defaultdict
from copy import copy
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast

from graphql import (
    ExecutionContext as GraphQLExecutionContext,
    GraphQLField,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)
from graphql.type.definition import GraphQLArgument

from strawberry.custom_scalar import ScalarDefinition, ScalarWrapper
from strawberry.enum import EnumDefinition
from strawberry.extensions import Extension
from strawberry.schema.types.concrete_type import TypeMap
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.cached_property import cached_property
from strawberry.utils.inspect import get_func_args

from ..printer import print_schema
from ..schema import Schema as BaseSchema
from ..schema.config import StrawberryConfig


class Schema(BaseSchema):
    def __init__(
        self,
        query: Optional[Type] = None,
        mutation: Optional[Type] = None,
        subscription: Optional[Type] = None,
        # TODO: we should update directives' type in the main schema
        directives: Iterable[Type] = (),
        types: Iterable[Type] = (),
        extensions: Iterable[Union[Type[Extension], Extension]] = (),
        execution_context_class: Optional[Type[GraphQLExecutionContext]] = None,
        config: Optional[StrawberryConfig] = None,
        scalar_overrides: Optional[
            Dict[object, Union[ScalarWrapper, ScalarDefinition]]
        ] = None,
        schema_directives: Iterable[object] = (),
        enable_federation_2: bool = False,
    ):

        query = self._get_federation_query_type(query)

        super().__init__(
            query=query,
            mutation=mutation,
            subscription=subscription,
            directives=directives,  # type: ignore
            types=types,
            extensions=extensions,
            execution_context_class=execution_context_class,
            config=config,
            scalar_overrides=scalar_overrides,
            schema_directives=schema_directives,
        )

        self._add_scalars()
        self._add_entities_to_query()

        if enable_federation_2:
            self._add_link_directives()
        else:
            self._remove_resolvable_field()

    def _get_federation_query_type(self, query: Optional[Type]) -> Type:
        """Returns a new query type that includes the _service field.

        If the query type is provided, it will be used as the base for the new
        query type. Otherwise, a new query type will be created.

        Federation needs the following two fields to be present in the query type:
        - _service: This field is used by the gateway to query for the capabilities
            of the federated service.
        - _entities: This field is used by the gateway to query for the entities
            that are part of the federated service.

        The _service field is added by default, but the _entities field is only
        added if the schema contains an entity type.
        """

        # note we don't add the _entities field here, as we need to know if the
        # schema contains an entity type first and we do that by leveraging
        # the schema converter type map, so we don't have to do that twice
        # TODO: ideally we should be able to do this without using the schema
        # converter, but for now this is the easiest way to do it
        # see `_add_entities_to_query`

        import strawberry
        from strawberry.tools.create_type import create_type
        from strawberry.tools.merge_types import merge_types

        @strawberry.type(name="_Service")
        class Service:
            sdl: str = strawberry.field(
                resolver=lambda: print_schema(self),
            )

        @strawberry.field(name="_service")
        def service() -> Service:
            return Service()

        fields = [service]

        FederationQuery = create_type(name="Query", fields=fields)

        if query is None:
            return FederationQuery

        query_type = merge_types(
            "Query",
            (
                FederationQuery,
                query,
            ),
        )

        # TODO: this should be probably done in merge_types
        if query._type_definition.extend:
            query_type._type_definition.extend = True  # type: ignore

        return query_type

    def _add_entities_to_query(self):
        entity_type = _get_entity_type(self.schema_converter.type_map)

        if not entity_type:
            return

        self._schema.type_map[entity_type.name] = entity_type
        fields = {"_entities": self._get_entities_field(entity_type)}

        # Copy the query type, update it to use the modified fields
        query_type = cast(GraphQLObjectType, self._schema.query_type)
        fields.update(query_type.fields)

        query_type = copy(query_type)
        query_type._fields = fields

        self._schema.query_type = query_type
        self._schema.type_map[query_type.name] = query_type

    def entities_resolver(self, root, info, representations):
        results = []

        for representation in representations:
            type_name = representation.pop("__typename")
            type_ = self.schema_converter.type_map[type_name]

            definition = cast(TypeDefinition, type_.definition)
            resolve_reference = definition.origin.resolve_reference

            func_args = get_func_args(resolve_reference)
            kwargs = representation

            if "info" in func_args:
                kwargs["info"] = info

            results.append(resolve_reference(**kwargs))

        return results

    def _add_scalars(self):
        self.Any = GraphQLScalarType("_Any")

        self._schema.type_map["_Any"] = self.Any

    def _remove_resolvable_field(self) -> None:
        # this might be removed when we remove support for federation 1
        # or when we improve how we print the directives
        from ..unset import UNSET
        from .schema_directives import Key

        for directive in self.schema_directives_in_use:
            if isinstance(directive, Key):
                directive.resolvable = UNSET

    @cached_property
    def schema_directives_in_use(self) -> List[object]:
        all_graphql_types = self._schema.type_map.values()

        directives = []

        for type_ in all_graphql_types:
            strawberry_definition = type_.extensions.get("strawberry-definition")

            if not strawberry_definition:
                continue

            directives.extend(strawberry_definition.directives)

            fields = getattr(strawberry_definition, "fields", [])
            values = getattr(strawberry_definition, "values", [])

            for field in chain(fields, values):
                directives.extend(field.directives)

        return directives

    def _add_link_directives(self):
        from .schema_directives import FederationDirective, Link

        directive_by_url = defaultdict(set)

        for directive in self.schema_directives_in_use:
            if isinstance(directive, FederationDirective):
                directive_by_url[directive.imported_from.url].add(
                    f"@{directive.imported_from.name}"
                )

        link_directives = tuple(
            Link(
                url=url,
                import_=list(sorted(directives)),
            )
            for url, directives in directive_by_url.items()
        )

        self.schema_directives = tuple(self.schema_directives) + link_directives

    def _get_entities_field(self, entity_type: GraphQLUnionType) -> GraphQLField:
        return GraphQLField(
            GraphQLNonNull(GraphQLList(entity_type)),
            args={
                "representations": GraphQLArgument(
                    GraphQLNonNull(GraphQLList(GraphQLNonNull(self.Any)))
                )
            },
            resolve=self.entities_resolver,
        )


def _get_entity_type(type_map: TypeMap):
    # https://www.apollographql.com/docs/apollo-server/federation/federation-spec/#resolve-requests-for-entities

    # To implement the _Entity union, each type annotated with @key
    # should be added to the _Entity union.

    federation_key_types = [
        type.implementation
        for type in type_map.values()
        if _has_federation_keys(type.definition)
        # TODO: check this
        and not isinstance(type.implementation, GraphQLInterfaceType)
    ]

    # If no types are annotated with the key directive, then the _Entity
    # union and Query._entities field should be removed from the schema.
    if not federation_key_types:
        return None

    entity_type = GraphQLUnionType("_Entity", federation_key_types)  # type: ignore

    def _resolve_type(self, value, _type):
        return self._type_definition.name

    entity_type.resolve_type = _resolve_type

    return entity_type


def _is_key(directive: Any) -> bool:
    from .schema_directives import Key

    return isinstance(directive, Key)


def _has_federation_keys(
    definition: Union[TypeDefinition, ScalarDefinition, EnumDefinition, StrawberryUnion]
) -> bool:
    if isinstance(definition, TypeDefinition):
        return any(_is_key(directive) for directive in definition.directives or [])

    return False

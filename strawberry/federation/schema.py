from collections import defaultdict
from copy import copy
from functools import partial
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast

from graphql import ExecutionContext as GraphQLExecutionContext
from graphql import (
    GraphQLError,
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


def create_catch_GraphQLError(get_result, definition):
    def catch_GraphQLError(representation):
        try:
            result = get_result(representation)
        except Exception as e:
            result = GraphQLError(
                f"Unable to resolve reference for {definition.origin}",
                original_error=e,
            )
        return result

    return catch_GraphQLError


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
            Dict[object, Union[Type, ScalarWrapper, ScalarDefinition]]
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

    def _entities_resolver(self, root, info, representations):
        results = []

        for representation in representations:
            type_name = representation.pop("__typename")
            type_ = self.schema_converter.type_map[type_name]

            definition = cast(TypeDefinition, type_.definition)

            if hasattr(definition.origin, "resolve_reference"):

                resolve_reference = definition.origin.resolve_reference

                func_args = get_func_args(resolve_reference)
                kwargs = representation

                # TODO: use the same logic we use for other resolvers
                if "info" in func_args:
                    kwargs["info"] = info

                get_result = partial(resolve_reference, **kwargs)
            else:
                from strawberry.arguments import convert_argument

                strawberry_schema = info.schema.extensions["strawberry-definition"]
                config = strawberry_schema.config
                scalar_registry = strawberry_schema.schema_converter.scalar_registry

                get_result = partial(
                    convert_argument,
                    representation,
                    type_=definition.origin,
                    scalar_registry=scalar_registry,
                    config=config,
                )

            try:
                result = get_result()
            except Exception as e:
                result = GraphQLError(
                    f"Unable to resolve reference for {definition.origin}",
                    original_error=e,
                )

            results.append(result)

        return results

    def entities_resolver(self, root, info, representations):
        results = []
        type_dict: Dict[str, Dict[str, Any]] = {}
        for index, representation in enumerate(representations):
            type_name = representation.pop("__typename")
            type_ = self.schema_converter.type_map[type_name]
            type_row = type_dict.get(type_name, None)
            if type_row is None:
                type_row = {
                    "type": type_,
                    "questions": [],
                    "indexes": [],
                    "results": [],
                    "lazy": False,
                    "iscoroutinefunction": False,
                    "get_result": lambda item: None,
                }
                type_dict[type_name] = type_row
                definition = cast(TypeDefinition, type_.definition)
                key_names = list(representation.keys())
                if hasattr(definition.origin, "resolve_references") and (
                    len(key_names) == 1
                ):
                    from inspect import iscoroutinefunction

                    key_name = key_names[0]
                    type_row["lazy"] = True

                    resolve_references = definition.origin.resolve_references
                    type_row["iscoroutinefunction"] = iscoroutinefunction(
                        resolve_references
                    )
                    func_args = get_func_args(resolve_references)

                    if key_name not in func_args:

                        def get_result(
                            representation,
                            type_row=type_row,
                            key_names=key_names,
                            definition=definition,
                            resolve_reference=resolve_references,
                            info=info,
                            func_args=func_args,
                        ):
                            result = (
                                "Got confused while trying use resolve_references for"
                                f" {definition.origin}. "
                                "Resolver resolve_references has not a prameter"
                                f" {key_names[0]}"
                            )

                            if result.startswith("G"):
                                raise Exception(result)
                            else:
                                return result

                    else:

                        def get_result_func(
                            representation,
                            type_row=type_row,
                            key_names=key_names,
                            definition=definition,
                            resolve_reference=resolve_references,
                            info=info,
                            func_args=func_args,
                        ):
                            key_name = key_names[0]
                            key_values = type_row["questions"]
                            kwargs = {}
                            kwargs[key_name] = list(
                                map(lambda item: item[key_name], key_values)
                            )
                            # TODO: use the same logic we use for other resolvers
                            if "info" in func_args:
                                kwargs["info"] = info
                            return resolve_reference(**kwargs)

                        get_result = create_catch_GraphQLError(
                            get_result_func, definition
                        )
                    type_row["get_result"] = get_result
                elif hasattr(definition.origin, "resolve_reference"):
                    type_row["lazy"] = False

                    resolve_reference = definition.origin.resolve_reference

                    func_args = get_func_args(resolve_reference)

                    # TODO: use the same logic we use for other resolvers
                    def get_result_func(
                        representation,
                        type_row=type_row,
                        key_names=key_names,
                        definition=definition,
                        resolve_reference=resolve_reference,
                        info=info,
                        func_args=func_args,
                    ):
                        if "info" in func_args:
                            return resolve_reference(info=info, **representation)
                        else:
                            return resolve_reference(**representation)

                    type_row["get_result"] = create_catch_GraphQLError(
                        get_result_func, definition
                    )
                else:
                    from strawberry.arguments import convert_argument
                    from strawberry.type import StrawberryType

                    type_row["lazy"] = False
                    strawberry_schema = info.schema.extensions["strawberry-definition"]
                    config = strawberry_schema.config
                    scalar_registry = strawberry_schema.schema_converter.scalar_registry

                    def create_get_result(
                        convert_argument,
                        type_par: Union[StrawberryType, type],  # = definition.origin,
                        scalar_registry_par: Dict[
                            object, Union[ScalarWrapper, ScalarDefinition]
                        ],  # = scalar_registry,
                        config_par: StrawberryConfig,  # = config,
                    ):
                        def newfunc(representation_par):
                            return convert_argument(
                                representation_par,
                                type_=type_par,
                                scalar_registry=scalar_registry_par,
                                config=config_par,
                            )

                        return newfunc

                    get_result = create_get_result(
                        convert_argument,
                        type_par=definition.origin,
                        scalar_registry_par=scalar_registry,
                        config_par=config,
                    )
                    type_row["get_result"] = create_catch_GraphQLError(
                        get_result, definition
                    )
            type_row["indexes"].append(index)
            type_row["questions"].append(representation)

        async def awaitable_wrapper(index, row):
            from inspect import isawaitable

            semaphore = row["semaphore"]
            list_of_indexes = row["indexes"]
            index_of = list_of_indexes.index(index)
            async with semaphore:
                list_of_results = row["results"]
                if isawaitable(list_of_results):
                    list_of_results = await list_of_results
                    row["results"] = list_of_results
                single_result = list_of_results[index_of]
            return single_result

        def sync_wrapper(index, row):
            list_of_indexes = row["indexes"]
            list_of_results = row["results"]
            index_of = list_of_indexes.index(index)
            single_result = list_of_results[index_of]
            return single_result

        indexed_results = []
        for _entity_name, row in type_dict.items():
            if row["lazy"]:
                from asyncio import BoundedSemaphore

                get_result = row["get_result"]
                result = get_result(None)
                current_indexed_results = []
                row["results"] = result
                if row["iscoroutinefunction"]:
                    row["semaphore"] = BoundedSemaphore(1)
                    current_indexed_results = [
                        (index, awaitable_wrapper(index, row))
                        for index in row["indexes"]
                    ]
                else:
                    current_indexed_results = [
                        (index, sync_wrapper(index, row)) for index in row["indexes"]
                    ]
                indexed_results.extend(current_indexed_results)
            else:
                get_result = row["get_result"]
                row["results"] = [get_result(item) for item in row["questions"]]
                current_indexed_results = [
                    (index, result)
                    for index, result in zip(row["indexes"], row["results"])
                ]
                indexed_results.extend(current_indexed_results)

        indexed_results.sort(key=lambda a: a[0])
        results = list(map(lambda item: item[1], indexed_results))
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

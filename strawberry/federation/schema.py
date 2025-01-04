from collections import defaultdict
from collections.abc import Iterable, Mapping
from functools import cached_property
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    NewType,
    Optional,
    Union,
    cast,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.printer import print_schema
from strawberry.schema import Schema as BaseSchema
from strawberry.types.base import (
    StrawberryContainer,
    StrawberryObjectDefinition,
    WithStrawberryObjectDefinition,
    get_object_definition,
)
from strawberry.types.info import Info
from strawberry.types.scalar import scalar
from strawberry.types.union import StrawberryUnion
from strawberry.utils.inspect import get_func_args

from .schema_directive import StrawberryFederationSchemaDirective

if TYPE_CHECKING:
    from graphql import ExecutionContext as GraphQLExecutionContext

    from strawberry.extensions import SchemaExtension
    from strawberry.federation.schema_directives import ComposeDirective
    from strawberry.schema.config import StrawberryConfig
    from strawberry.schema_directive import StrawberrySchemaDirective
    from strawberry.types.enum import EnumDefinition
    from strawberry.types.scalar import ScalarDefinition, ScalarWrapper


FederationAny = scalar(NewType("_Any", object), name="_Any")  # type: ignore


class Schema(BaseSchema):
    def __init__(
        self,
        query: Optional[type] = None,
        mutation: Optional[type] = None,
        subscription: Optional[type] = None,
        # TODO: we should update directives' type in the main schema
        directives: Iterable[type] = (),
        types: Iterable[type] = (),
        extensions: Iterable[Union[type["SchemaExtension"], "SchemaExtension"]] = (),
        execution_context_class: Optional[type["GraphQLExecutionContext"]] = None,
        config: Optional["StrawberryConfig"] = None,
        scalar_overrides: Optional[
            dict[object, Union[type, "ScalarWrapper", "ScalarDefinition"]]
        ] = None,
        schema_directives: Iterable[object] = (),
        enable_federation_2: bool = False,
    ) -> None:
        query = self._get_federation_query_type(query, mutation, subscription, types)
        types = [*types, FederationAny]

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

        self.schema_directives = list(schema_directives)

        if enable_federation_2:
            composed_directives = self._add_compose_directives()
            self._add_link_directives(composed_directives)  # type: ignore
        else:
            self._remove_resolvable_field()

    def _get_federation_query_type(
        self,
        query: Optional[type[WithStrawberryObjectDefinition]],
        mutation: Optional[type[WithStrawberryObjectDefinition]],
        subscription: Optional[type[WithStrawberryObjectDefinition]],
        additional_types: Iterable[type[WithStrawberryObjectDefinition]],
    ) -> type:
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

        entity_type = _get_entity_type(query, mutation, subscription, additional_types)

        if entity_type:
            self.entities_resolver.__annotations__["return"] = list[
                Optional[entity_type]  # type: ignore
            ]

            entities_field = strawberry.field(
                name="_entities", resolver=self.entities_resolver
            )

            fields.insert(0, entities_field)

        FederationQuery = create_type(name="Query", fields=fields)

        if query is None:
            return FederationQuery

        query_type = merge_types(
            "Query",
            (FederationQuery, query),
        )

        # TODO: this should be probably done in merge_types
        if query.__strawberry_definition__.extend:
            query_type.__strawberry_definition__.extend = True  # type: ignore

        return query_type

    def entities_resolver(
        self, info: Info, representations: list[FederationAny]
    ) -> list[FederationAny]:
        results = []

        for representation in representations:
            type_name = representation.pop("__typename")
            type_ = self.schema_converter.type_map[type_name]

            definition = cast(StrawberryObjectDefinition, type_.definition)

            if hasattr(definition.origin, "resolve_reference"):
                resolve_reference = definition.origin.resolve_reference

                func_args = get_func_args(resolve_reference)
                kwargs = representation

                # TODO: use the same logic we use for other resolvers
                if "info" in func_args:
                    kwargs["info"] = info

                try:
                    result = resolve_reference(**kwargs)
                except Exception as e:  # noqa: BLE001
                    result = e
            else:
                from strawberry.types.arguments import convert_argument

                config = info.schema.config
                scalar_registry = info.schema.schema_converter.scalar_registry

                try:
                    result = convert_argument(
                        representation,
                        type_=definition.origin,
                        scalar_registry=scalar_registry,
                        config=config,
                    )
                except Exception:  # noqa: BLE001
                    result = TypeError(f"Unable to resolve reference for {type_name}")

            results.append(result)

        return results

    def _remove_resolvable_field(self) -> None:
        # this might be removed when we remove support for federation 1
        # or when we improve how we print the directives
        from strawberry.types.unset import UNSET

        from .schema_directives import Key

        for directive in self.schema_directives_in_use:
            if isinstance(directive, Key):
                directive.resolvable = UNSET

    @cached_property
    def schema_directives_in_use(self) -> list[object]:
        all_graphql_types = self._schema.type_map.values()

        directives: list[object] = []

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

    def _add_link_for_composed_directive(
        self,
        directive: "StrawberrySchemaDirective",
        directive_by_url: Mapping[str, set[str]],
    ) -> None:
        if not isinstance(directive, StrawberryFederationSchemaDirective):
            return

        if not directive.compose_options:
            return

        import_url = directive.compose_options.import_url
        name = self.config.name_converter.from_directive(directive)

        # import url is required by Apollo Federation, this might change in
        # future to be optional, so for now, when it is not passed we
        # define a mock one. The URL isn't used for validation anyway.
        if import_url is None:
            import_url = f"https://directives.strawberry.rocks/{name}/v0.1"

        directive_by_url[import_url].add(f"@{name}")

    def _add_link_directives(
        self, additional_directives: Optional[list[object]] = None
    ) -> None:
        from .schema_directives import FederationDirective, Link

        directive_by_url: defaultdict[str, set[str]] = defaultdict(set)

        additional_directives = additional_directives or []

        for directive in self.schema_directives_in_use + additional_directives:
            definition = directive.__strawberry_directive__  # type: ignore

            self._add_link_for_composed_directive(definition, directive_by_url)

            if isinstance(directive, FederationDirective):
                directive_by_url[directive.imported_from.url].add(
                    f"@{directive.imported_from.name}"
                )

        link_directives: list[object] = [
            Link(
                url=url,
                import_=sorted(directives),  # type: ignore[arg-type]
            )
            for url, directives in directive_by_url.items()
        ]

        self.schema_directives = self.schema_directives + link_directives

    def _add_compose_directives(self) -> list["ComposeDirective"]:
        from .schema_directives import ComposeDirective

        compose_directives: list[ComposeDirective] = []

        for directive in self.schema_directives_in_use:
            definition = directive.__strawberry_directive__  # type: ignore

            is_federation_schema_directive = isinstance(
                definition, StrawberryFederationSchemaDirective
            )

            if is_federation_schema_directive and definition.compose_options:
                name = self.config.name_converter.from_directive(definition)

                compose_directives.append(
                    ComposeDirective(
                        name=f"@{name}",
                    )
                )

        self.schema_directives = self.schema_directives + compose_directives

        return compose_directives

    def _warn_for_federation_directives(self) -> None:
        # this is used in the main schema to raise if there's a directive
        # that's for federation, but in this class we don't want to warn,
        # since it is expected to have federation directives

        pass


def _get_entity_type(
    query: Optional[type[WithStrawberryObjectDefinition]],
    mutation: Optional[type[WithStrawberryObjectDefinition]],
    subscription: Optional[type[WithStrawberryObjectDefinition]],
    additional_types: Iterable[type[WithStrawberryObjectDefinition]],
) -> Optional[StrawberryUnion]:
    # recursively iterate over the schema to find all types annotated with @key
    # if no types are annotated with @key, then the _Entity union and Query._entities
    # field should not be added to the schema

    entity_types = set()

    # need a stack to keep track of the types we need to visit
    stack: list[Any] = [query, mutation, subscription, *additional_types]

    seen = set()

    while stack:
        type_ = stack.pop()

        if type_ is None:
            continue

        while isinstance(type_, StrawberryContainer):
            type_ = type_.of_type

        type_definition = get_object_definition(type_, strict=False)

        if type_definition is None:
            continue

        if type_definition.is_object_type and _has_federation_keys(type_definition):
            entity_types.add(type_)

        for field in type_definition.fields:
            if field.type and field.type in seen:
                continue

            seen.add(field.type)
            stack.append(field.type)

    if not entity_types:
        return None

    sorted_types = sorted(entity_types, key=lambda t: t.__strawberry_definition__.name)

    return StrawberryUnion(
        "_Entity",
        type_annotations=tuple(StrawberryAnnotation(type_) for type_ in sorted_types),
    )


def _is_key(directive: Any) -> bool:
    from .schema_directives import Key

    return isinstance(directive, Key)


def _has_federation_keys(
    definition: Union[
        StrawberryObjectDefinition,
        "ScalarDefinition",
        "EnumDefinition",
        "StrawberryUnion",
    ],
) -> bool:
    if isinstance(definition, StrawberryObjectDefinition):
        return any(_is_key(directive) for directive in definition.directives or [])

    return False


__all__ = ["Schema"]

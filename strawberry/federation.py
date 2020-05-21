from graphql import (
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLType,
    GraphQLUnionType,
)

from .field import strawberry_field
from .printer import print_schema
from .schema import Schema as BaseSchema
from .type import _process_type
from .type_registry import get_strawberry_type_for_graphql_type


def type(cls=None, *args, **kwargs):
    def wrap(cls):
        keys = kwargs.pop("keys", [])
        extend = kwargs.pop("extend", False)

        wrapped = _process_type(cls, *args, **kwargs)
        wrapped._federation_keys = keys
        wrapped._federation_extend = extend

        return wrapped

    if cls is None:
        return wrap

    return wrap(cls)


def strawberry_federation_field(*args, **kwargs):
    provides = kwargs.pop("provides", "")
    requires = kwargs.pop("requires", "")
    external = kwargs.pop("external", False)

    metadata = kwargs.get("metadata") or {}
    metadata["federation"] = {
        "provides": provides,
        "external": external,
        "requires": requires,
    }
    kwargs["metadata"] = metadata

    field = strawberry_field(*args, **kwargs)

    return field


def field(wrap=None, *args, **kwargs):
    field = strawberry_federation_field(*args, **kwargs)

    if wrap is None:
        return field

    return field(wrap)


def entities_resolver(root, info, representations):
    results = []

    for representation in representations:
        type_name = representation.pop("__typename")
        graphql_type = info.schema.get_type(type_name)

        result = get_strawberry_type_for_graphql_type(graphql_type).resolve_reference(
            **representation
        )
        results.append(result)

    return results


def has_federation_keys(graphql_type: GraphQLType):
    strawberry_type = get_strawberry_type_for_graphql_type(graphql_type)

    if strawberry_type and getattr(strawberry_type, "_federation_keys", []):
        return True

    return False


class Schema(BaseSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._extend_query_type()

    def _extend_query_type(self):
        @type(name="_Service")
        class Service:
            sdl: str

        Any = GraphQLScalarType("_Any")

        fields = {
            "_service": GraphQLField(
                GraphQLNonNull(Service.graphql_type),
                resolve=lambda _, info: Service(sdl=print_schema(info.schema)),
            )
        }

        entities_type = self._get_entity_type()

        if entities_type:
            self.type_map[entities_type.name] = entities_type

            fields["_entities"] = GraphQLField(
                GraphQLNonNull(GraphQLList(entities_type)),
                args={
                    "representations": GraphQLNonNull(GraphQLList(GraphQLNonNull(Any)))
                },
                resolve=entities_resolver,
            )

        fields.update(self.query_type.fields)

        self.query_type = GraphQLObjectType(
            name=self.query_type.name,
            description=self.query_type.description,
            fields=fields,
        )

        self.type_map["_Any"] = Any
        self.type_map["_Service"] = Service.graphql_type
        self.type_map[self.query_type.name] = self.query_type

    def _get_entity_type(self):
        # https://www.apollographql.com/docs/apollo-server/federation/federation-spec/#resolve-requests-for-entities

        # To implement the _Entity union, each type annotated with @key
        # should be added to the _Entity union.

        federation_key_types = [
            graphql_type
            for graphql_type in self.type_map.values()
            if has_federation_keys(graphql_type)
        ]

        # If no types are annotated with the key directive, then the _Entity
        # union and Query._entities field should be removed from the schema.
        if not federation_key_types:
            return None

        entity_type = GraphQLUnionType("_Entity", federation_key_types)

        def _resolve_type(self, value, _type):
            return self.graphql_type

        entity_type.resolve_type = _resolve_type

        return entity_type

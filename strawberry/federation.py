from graphql import (
    GraphQLField,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)

from .field import strawberry_field
from .printer import print_schema
from .schema import Schema as BaseSchema
from .type import _process_type


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

        result = graphql_type._strawberry_type.resolve_reference(**representation)
        results.append(result)

    return results


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
        federation_key_types = []

        for graphql_type in self.type_map.values():
            if hasattr(graphql_type, "_strawberry_type"):
                if graphql_type._strawberry_type and getattr(
                    graphql_type._strawberry_type, "_federation_keys", []
                ):
                    federation_key_types.append(graphql_type)

        if federation_key_types:
            entity_type = GraphQLUnionType("_Entity", federation_key_types)

            def _resolve_type(self, value, _type):
                return self.graphql_type

            entity_type.resolve_type = _resolve_type

            return entity_type

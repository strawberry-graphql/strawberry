from graphql import GraphQLField, GraphQLObjectType, GraphQLString

from .type_converter import get_graphql_type_for_annotation

TEST_ = """type MyType {
    name: String!
}"""


def _get_resolver(cls, field_name):
    def _resolver(obj, info):
        field_resolver = getattr(cls, field_name)

        if getattr(field_resolver, "_is_field", False):
            # not sure why I need to pass the class
            return field_resolver(cls, obj, info)

        return resolver

    return _resolver


def _get_fields(cls):
    cls_annotations = cls.__dict__.get("__annotations__", {})

    cls_annotations.update(
        {
            key: value.__annotations__["return"]
            for key, value in cls.__dict__.items()
            if getattr(value, "_is_field", False)
        }
    )

    return {
        key: GraphQLField(
            get_graphql_type_for_annotation(value), resolve=_get_resolver(cls, key)
        )
        for key, value in cls_annotations.items()
    }


def type(cls):
    def wrap():
        def repr_(self):
            return TEST_

        setattr(cls, "__repr__", repr_)

        cls._fields = _get_fields(cls)
        cls.field = GraphQLObjectType(name=cls.__name__, fields=cls._fields)

        return cls

    return wrap()

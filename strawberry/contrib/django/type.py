import strawberry
from strawberry.contrib.django.converter import convert_django_field
from strawberry.type import type as strawberry_type


def model_type(cls=None, *, model=None, fields=[], is_input=False, is_interface=False):
    """Defines a Django model type and generates resolvers for each field.

    Example usage:

    >>> @strawberry.model_type(model=TestModel):
    >>> class TestModelType:
    >>>     pass
    """

    def wrap(cls):

        meta = getattr(cls, "Meta", None)
        _model = getattr(meta, "model", model)
        _fields = getattr(meta, "fields", fields)
        _is_input = getattr(meta, "is_input", is_input)
        _is_interface = getattr(meta, "is_interface", is_interface)

        if not _model:
            raise ValueError("Each model type must define a model")

        for field in _model._meta.get_fields():
            if _fields != "__all__" and field.name not in _fields:
                continue

            field_type = convert_django_field(field)

            if hasattr(cls, field.name):
                continue

            if _is_input:
                if field.name == "id":
                    continue

                if not hasattr(cls, "__annotations__"):
                    cls.__annotations__ = {}

                cls.__annotations__[field.name] = field_type
            else:

                def create_resolver(field_name):
                    @strawberry.field
                    def resolver(self, info) -> field_type:
                        value = getattr(self, field_name)
                        return value

                    return resolver

                setattr(cls, field.name, create_resolver(field.name))

        _type = strawberry_type(
            cls,
            is_input=_is_input,
            is_interface=_is_interface,
            description=cls.__doc__ or _model.__doc__,
        )

        return _type

    if cls is None:
        return wrap

    return wrap(cls)

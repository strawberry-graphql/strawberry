import strawberry
from strawberry.contrib.django.converter import convert_django_field
from strawberry.type import type as strawberry_type


def model_type(
    cls=None,
    *,
    model=None,
    exclude_fields=[],
    only_fields=[],
    is_input=False,
    is_interface=False,
    description=None
):
    """Defines a Django model type and generates resolvers for each field.

    Example usage:

    >>> @strawberry.model_type(model=TestModel):
    >>> class TestModelType:
    >>>     pass
    """

    if not model:
        raise ValueError("Each model type must define a model")

    def wrap(cls):

        for field in model._meta.get_fields():
            if exclude_fields and field.name in exclude_fields:
                continue

            if only_fields and field.name not in only_fields:
                continue

            field_type = convert_django_field(field)

            if hasattr(cls, field.name):
                continue

            if is_input:
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
            is_input=is_input,
            is_interface=is_interface,
            description=description or model.__doc__,
        )

        return _type

    if cls is None:
        return wrap

    return wrap(cls)

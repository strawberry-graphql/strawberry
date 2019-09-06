from strawberry.contrib.django.converter import convert_django_field_to_resolver
from strawberry.type import type as strawberry_type


def model_type(
    cls=None, *, model=None, is_input=False, is_interface=False, description=None
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
            resolver = convert_django_field_to_resolver(field)

            setattr(cls, field.name, resolver)

        return strawberry_type(
            cls,
            is_input=is_input,
            is_interface=is_interface,
            description=description or model.__doc__,
        )

    if cls is None:
        return wrap

    return wrap(cls)

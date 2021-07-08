from dataclasses import field as dataclasses_field, make_dataclass
from typing import List, Type

import strawberry
from strawberry.field import StrawberryField


def create_type(name: str, fields: List[StrawberryField]) -> Type:
    """Create a Strawberry type from a list of StrawberryFields

    >>> @strawberry.field
    >>> def hello(info) -> str:
    >>>     return "World"
    >>>
    >>> Query = create_type(name="Query", fields=[hello])
    """

    if len(fields) == 0:
        raise ValueError(f'Can\'t create type "{name}" with no fields')

    dataclass_fields = []

    for field in fields:
        if not isinstance(field, StrawberryField):
            raise TypeError("Field is not an instance of StrawberryField")

        if field.graphql_name is None:
            raise ValueError(
                (
                    "Field doesn't have a name. Fields passed to "
                    "`create_type` must define a name by passing the "
                    "`name` argument to `strawberry.field`."
                )
            )

        dataclass_fields.append(
            (
                field.graphql_name,
                field.type,
                dataclasses_field(default=field),
            )
        )

    cls = make_dataclass(name, fields=dataclass_fields)

    return strawberry.type(cls)

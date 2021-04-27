from dataclasses import field as dataclasses_field, make_dataclass
from typing import List, Type, cast

import strawberry
from strawberry.field import StrawberryField


def create_type(name: str, fields: List[StrawberryField]) -> Type:
    cls = make_dataclass(
        name,
        fields=[
            (
                cast(str, field.graphql_name),
                field.type,
                dataclasses_field(default=field),
            )
            for field in fields
        ],
    )

    return strawberry.type(cls)

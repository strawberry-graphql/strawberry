Release type: minor

This release add support for converting the enum value names
from `NameConverter`. It looks like this:


```python
from enum import Enum

import strawberry
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.name_converter import NameConverter


class EnumNameConverter(NameConverter):
    def from_enum_value(self, enum: EnumDefinition, enum_value: EnumValue) -> str:
        return f"{super().from_enum_value(enum, enum_value)}_enum_value"


@strawberry.enum
class MyEnum(Enum):
    A = "a"
    B = "b"


@strawberry.type
class Query:
    a_enum: MyEnum


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(name_converter=EnumNameConverter()),
)
```

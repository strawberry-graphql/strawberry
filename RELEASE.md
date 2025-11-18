Release type: minor

This release changes `_enum_definition` to `__strawberry_definition__`, this is a follow up to previous
internal changes. If you were relying on `_enum_definition` you should update your code to use `__strawberry_definition__`.

We also expose `has_enum_definition` to check if a type is a strawberry enum definition.

```python
from enum import Enum
import strawberry
from strawberry.types.enum import StrawberryEnumDefinition, has_enum_definition


@strawberry.enum
class ExampleEnum(Enum):
    pass


has_enum_definition(ExampleEnum)  # True
# Now you can use ExampleEnum.__strawberry_definition__ to access the enum definition
```

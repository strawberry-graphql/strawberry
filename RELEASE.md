Release type: patch

Fix an issue where there was no clean way to mark a Pydantic field as deprecated, add permission classes, or add directives. Now you can use the short field syntax to do all three.

```python
import pydantic
import strawberry

class MyModel(pydantic.BaseModel):
    age: int
    name: str

@strawberry.experimental.pydantic.type(MyModel)
class MyType:
    age: strawberry.auto
    name: strawberry.auto = strawberry.field(
        deprecation_reason="Because",
        permission_classes=[MyPermission],
        directives=[MyDirective],
    )
```

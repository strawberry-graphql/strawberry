Release type: patch

This release fixes an issue that prevented using generic
that had a field of type enum. The following works now:

```python
@strawberry.enum
class EstimatedValueEnum(Enum):
    test = "test"
    testtest = "testtest"


@strawberry.type
class EstimatedValue(Generic[T]):
    value: T
    type: EstimatedValueEnum


@strawberry.type
class Query:
    @strawberry.field
    def estimated_value(self) -> Optional[EstimatedValue[int]]:
        return EstimatedValue(value=1, type=EstimatedValueEnum.test)
```

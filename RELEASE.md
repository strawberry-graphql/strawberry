Release type: minor

This release improves how we deal with custom scalars. Instead of being global
they are now scoped to the schema. This allows you to have multiple schemas in
the same project with differnet scalars.

Also you can now override the built in scalars with your own custom
implementation. Out of the box Strawberry provides you with custom scalars for
common Python types like `datetime` and `Decimal`. If you require a custom
implementation of one of these built in scalars you can how subclass the
`Schema` class and override the `get_scalar` function to return your own custom
implementation:

```python
from datetime import datetime, timezone
import strawberry

EpocDateTime = strawberry.scalar(
    datetime,
    serialize=lambda value: int(value.timestamp()),
    parse_value=lambda value: datetime.fromtimestamp(int(value), timezone.utc),
)

class MySchema(strawberry.Schema):
    def get_scalar(self, scalar):
        if scalar == datetime:
            return EpocDateTime
        return super().get_scalar(scalar)

@strawberry.type
class Query:
    @strawberry.field
    def current_time(self) -> datetime:
        return datetime.now()

schema = MySchema(Query)
result = schema.execute_sync("{ currentTime }")
assert result.data == {"currentTime": 1628683200}
```

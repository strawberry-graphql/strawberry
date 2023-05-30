Release type: patch

This release fixes a bug in experimental.pydantic whereby `Optional` type annotations weren't exactly aligned between strawberry type and pydantic model.

Previously this would have caused the series field to be non-nullable in graphql.
```python
from typing import Optional
from pydantic import BaseModel, Field
import strawberry


class VehicleModel(BaseModel):
    series: Optional[str] = Field(default="")


@strawberry.experimental.pydantic.type(model=VehicleModel, all_fields=True)
class VehicleModelType:
    pass
```

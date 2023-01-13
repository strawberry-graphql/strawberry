Release type: minor

Support constrained float field types in Pydantic models.

i.e.

```python
import pydantic

class Model(pydantic.BaseModel):
    field: pydantic.confloat(le=100.0)
	equivalent_field: float = pydantic.Field(le=100.0)
```

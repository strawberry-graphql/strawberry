Release type: patch

Fix missing custom `resolve_reference` for using pydantic with federation

i.e:

```python
import typing
from pydantic import BaseModel
import strawberry
from strawberry.federation.schema_directives import Key


class ProductInDb(BaseModel):
    upc: str
    name: str


@strawberry.experimental.pydantic.type(
    model=ProductInDb, directives=[Key(fields="upc", resolvable=True)]
)
class Product:
    upc: str
    name: str

    @classmethod
    def resolve_reference(cls, upc):
        return Product(upc=upc, name="")
```

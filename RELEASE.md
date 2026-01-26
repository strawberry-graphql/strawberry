Release type: patch

This release adds support for field extensions in experimental pydantic types.

Previously, when using `@strawberry.experimental.pydantic.type()` decorator, field extensions defined with `strawberry.field(extensions=[...])` were not being propagated to the generated Strawberry fields. This meant extensions like authentication, caching, or result transformation couldn't be used with pydantic-based types.

This fix ensures that extensions are properly preserved when converting pydantic fields to Strawberry fields, enabling the full power of field extensions across the pydantic integration.

Examples:

**Permission-based field masking:**

```python
from pydantic import BaseModel
from typing import Optional
import strawberry
from strawberry.experimental.pydantic import type as pyd_type
from strawberry.extensions.field_extension import FieldExtension

class PermissionExtension(FieldExtension):
    def resolve(self, next_, source, info, **kwargs):
        # Check permission, return None if denied
        if not check_field_access(info.context.user, info.field_name, source.id):
            return None
        return next_(source, info, **kwargs)

class UserModel(BaseModel):
    id: int
    fname: str
    email: str
    phone: str

perm_ext = PermissionExtension()

@pyd_type(model=UserModel)
class UserGQL:
    # Public fields - just use auto
    id: strawberry.auto
    fname: strawberry.auto
    
    # Protected fields - attach extension
    email: Optional[str] = strawberry.field(extensions=[perm_ext])
    phone: Optional[str] = strawberry.field(extensions=[perm_ext])
```

**Simple transformation extension:**

```python
class UpperCaseExtension(FieldExtension):
    def resolve(self, next_, source, info, **kwargs):
        result = next_(source, info, **kwargs)
        return str(result).upper()

class ProductModel(BaseModel):
    name: str

@pyd_type(model=ProductModel)
class Product:
    name: str = strawberry.field(extensions=[UpperCaseExtension()])
```

Release type: patch

This release fixes issues with explicit field definitions in experimental pydantic types:

**`all_fields=True` now respects explicit field definitions**: Previously, using `all_fields=True` would override any explicitly defined fields in the strawberry type. Now, explicit definitions take precedence, allowing you to:

- Mark fields as `strawberry.Private` to hide them from the GraphQL schema
- Add field extensions (e.g., for authentication, caching, transformations)
- Override field types
- Add custom resolvers

The warning "Using all_fields overrides any explicitly defined fields" has been removed since combining `all_fields=True` with explicit definitions is now a valid and useful pattern.

**Private fields are auto-populated from pydantic models**: When a `strawberry.Private` field has the same name as a pydantic model field, `from_pydantic()` will automatically populate it from the model (can be overridden via the `extra` dict).

Example:

```python
from pydantic import BaseModel
import strawberry
from strawberry.experimental.pydantic import type as pyd_type
from strawberry.extensions.field_extension import FieldExtension


class MaskExtension(FieldExtension):
    def resolve(self, next_, source, info, **kwargs):
        result = next_(source, info, **kwargs)
        return result[:3] + "****" if result else result


class UserModel(BaseModel):
    name: str
    email: str
    password: str


@pyd_type(model=UserModel, all_fields=True)
class User:
    # Add extension to mask email in responses
    email: str = strawberry.field(extensions=[MaskExtension()])
    # Hide password from GraphQL schema entirely
    password: strawberry.Private[str]


# name and email are exposed in schema, password is not
# email will be masked by the extension
pydantic_user = UserModel(name="Alice", email="alice@example.com", password="secret")
strawberry_user = User.from_pydantic(pydantic_user)

# Private field is still accessible internally
print(strawberry_user.password)  # "secret"
```

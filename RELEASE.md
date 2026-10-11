---
release type: patch
---

This release fixes `Annotated` fields sharing a `strawberry.field()` resolving
their `graphql_type` in the wrong module.

When the same `strawberry.field()` was used by types in different modules, for
example through a type alias, the first type to be processed decided where a
string `graphql_type` was looked up, and every other type used that module too:

```python
# aliases.py
AddressField = Annotated[str, strawberry.field(graphql_type="Address")]


# shop.py
@strawberry.type
class Shop:
    address: AddressField  # uses shop.Address


# warehouse.py
@strawberry.type
class Warehouse:
    address: AddressField  # used shop.Address too, now uses warehouse.Address
```

Each type now resolves it in its own module, like other annotations.

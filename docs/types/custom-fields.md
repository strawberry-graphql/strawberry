---
title: Custom Fields
---

# Custom Fields

<Warning>

This is an advanced feature of Strawberry which you might not need. It can be
tempting to build complicated custom fields to abstract duplicated patterns in
your schema but you might find that it just results in less maintainable code
that is harder to reason about. Try keeping things inline before implementing a 
custom field.

</Warning>

You can extend the default `StrawberryField` to customise it's return value.
This is useful to encapsulate common resolver logic across your API and is a
form of [metaprogramming](https://en.wikipedia.org/wiki/Metaprogramming).

# Example

Here we define an `UpperCaseField` that always converts the return value from a
resolver into uppercase.

```python
import strawberry
from strawberry.field import Strawberry

class UpperCaseField(StrawberryField):
    def get_result(self, source, info, arguments):
        result = super().get_result(source, info, arguments)
        return result.upper()

@strawberry.type
class Query:
    name: str = UpperCaseField(default="Patrick")

    @UpperCaseField()
    def alt_name() -> str:
        return "patrick91"
```

Note how we can use `UpperCaseField` in all the same places that we could use
`strawberry.field`. It takes all the same arguments as well.

```graphql+json
{
  name
  altName
}

---

{
  "data": {
    "name": "PATRICK",
    "altName": PATRICK91"
  }
}
```

---
release type: patch
---

This release fixes fields with an argument named `source` failing when they use
permission classes or field extensions.

Strawberry passes a field's arguments to permissions and extensions as keyword
arguments, so an argument called `source` collided with the parent object
parameter and raised `got multiple values for argument 'source'`, even when the
argument was not provided. The `next_`, `source` and `info` parameters of the
built-in permission and field extension hooks are now positional-only, so a
field argument named `source` reaches `**kwargs` instead.

If you write your own `has_permission` or field extension and need an argument
named `source`, declare the leading parameters as positional-only too:

```python
def has_permission(self, source, info, /, **kwargs) -> bool: ...
```

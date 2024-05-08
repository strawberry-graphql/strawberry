Release type: patch

**Deprecations:** This release deprecates the `Starlite` integration in favour of the `LiteStar` integration.
Refer to the [LiteStar](./litestar.md) integration for more information.
LiteStar is a [renamed](https://litestar.dev/about/organization.html#litestar-and-starlite) and upgraded version of Starlite.

Before:

```python
from strawberry.starlite import make_graphql_controller
```

After:

```python
from strawberry.litestar import make_graphql_controller
```

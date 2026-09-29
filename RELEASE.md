---
release type: minor
social_messages:
  x: >-
    Strawberry {version} is out! This release adds support for configuring your
    schema with a plain dictionary, e.g. `config={"auto_camel_case": False}`. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release adds support for configuring your
    schema with a plain dictionary, e.g. `config={"auto_camel_case": False}`,
    so you no longer need to import and instantiate `StrawberryConfig` for
    simple configuration.
---

This release adds support for passing a plain dictionary as the `config`
argument of `strawberry.Schema` (and `strawberry.federation.Schema`):

```python
schema = strawberry.Schema(query=Query, config={"auto_camel_case": False})
```

The dictionary is typed as `StrawberryConfigDict` (a `TypedDict` with all keys
optional) and is normalized to a `StrawberryConfig` internally, so every part
of the codebase keeps working with attribute access. Passing a
`StrawberryConfig` instance continues to work exactly as before.

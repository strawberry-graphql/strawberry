---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! You can now configure your schema with a
    plain dictionary, no need to instantiate StrawberryConfig for simple
    setups. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds support for passing a
    plain dictionary as the config argument of strawberry.Schema, so simple
    schema configuration no longer requires importing and instantiating
    StrawberryConfig.
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

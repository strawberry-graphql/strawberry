---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds support for optional
    `info` parameters in resolvers, so `info: strawberry.Info | None = None`
    now works and keeps type checkers happy. 🍓
    {{https://strawberry.rocks/release/{version}}}
  linkedin: >-
    {project_name} {version} is out. This release adds support for optional
    `info` parameters in resolvers. Annotating a resolver with
    `info: strawberry.Info | None = None` now injects the execution info as
    usual, so resolvers that are also called directly from Python no longer
    need an annotation that every type checker rejects.
---

This release adds support for optional `info` parameters in resolvers.

Previously only a bare `strawberry.Info` annotation was recognized, so a
resolver that is also called directly from Python had to be written as
`info: strawberry.Info = None` — an annotation every type checker rejects.

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, info: strawberry.Info | None = None) -> str:
        return "from GraphQL" if info else "standalone"
```

`Optional[Info]`, `Union[Info, None]`, generic forms such as
`Info[Context, RootValue] | None`, subclasses of `Info` used with
`StrawberryConfig(info_class=...)`, type aliases, and qualified string or
forward reference annotations such as `"strawberry.Info | None"` are all
recognized.

Unions with more than one non-`None` member, such as `Info | str | None`, are
still rejected, and this change does not affect the `Parent` or
`DirectiveValue` reserved parameters.

An optional `info` parameter is now always injected by Strawberry and never
appears as a field argument in the schema, including when a scalar override is
registered for `Info`.

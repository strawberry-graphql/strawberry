---
release type: patch
---

This release fixes the Python plugin of `strawberry codegen` generating invalid
Python when a GraphQL name is a Python keyword. Fields, aliases, variables,
input fields and enum values named like `from`, `class` or `import` used to be
emitted as-is (for example `from: str`), which is a `SyntaxError`. They now get
a trailing underscore, following PEP 8, the same way `strawberry schema-codegen`
already names them:

```graphql
query GetMessage($class: String) {
  from
}
```

```python
class GetMessageResult:
    from_: str


class GetMessageVariables:
    class_: Optional[str]
```

Enum values keep their GraphQL name as the value (`from_ = "from"`). The
TypeScript plugin is unchanged, since keywords are valid property names there.

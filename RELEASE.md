---
release type: patch
social_messages:
  x: >-
    Strawberry {version} is out! This release fixes schema codegen generating
    invalid Python when a GraphQL enum value is a Python keyword. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release fixes schema codegen so that
    GraphQL enum values that are Python keywords (like `class` or `import`) now
    generate valid Python instead of code that fails to import.
---

This release fixes schema codegen that generated invalid Python when a GraphQL
enum value is a Python keyword.

Previously, an enum such as:

```graphql
enum Example {
  class
  import
}
```

generated Python that could not be imported, because `class` and `import` are
reserved keywords:

```python
@strawberry.enum
class Example(Enum):
    class = "class"  # SyntaxError
    import = "import"
```

Strawberry now aliases these members and preserves the original GraphQL name via
`strawberry.enum_value`, matching how keyword field names are already handled:

```python
@strawberry.enum
class Example(Enum):
    class_ = strawberry.enum_value("class", name="class")
    import_ = strawberry.enum_value("import", name="import")
```

Release type: patch

This release adjusts the schema printer to avoid printing a schema directive
value set to `UNSET` as `""` (empty string).

For example, the following:

```python
@strawberry.input
class FooInput:
    a: str | None = strawberry.UNSET
    b: str | None = strawberry.UNSET


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class FooDirective:
    input: FooInput


@strawberry.type
class Query:
    @strawberry.field(directives=[FooDirective(input=FooInput(a="aaa"))])
    def foo(self, info) -> str: ...
```

Would previously print as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { a: "aaa", b: "" })
}

input FooInput {
  a: String
  b: String
}
```

Now it will be correctly printed as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { a: "aaa" })
}

input FooInput {
  a: String
  b: String
}
```

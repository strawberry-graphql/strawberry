Release type: patch

This release fixes an issue where directives with input types using snake_case
would not be printed in the schema.

For example, the following:

```python
@strawberry.input
class FooInput:
    hello: str
    hello_world: str


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class FooDirective:
    input: FooInput


@strawberry.type
class Query:
    @strawberry.field(
        directives=[
            FooDirective(input=FooInput(hello="hello", hello_world="hello world")),
        ]
    )
    def foo(self, info) -> str: ...
```

Would previously print as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String! @fooDirective(input: { hello: "hello" })
}

input FooInput {
  hello: String!
  hello_world: String!
}
```

Now it will be correctly printed as:

```graphql
directive @fooDirective(
  input: FooInput!
  optionalInput: FooInput
) on FIELD_DEFINITION

type Query {
  foo: String!
    @fooDirective(input: { hello: "hello", helloWorld: "hello world" })
}

input FooInput {
  hello: String!
  hello_world: String!
}
```

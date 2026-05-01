Release type: patch

Previously attributes which were not camelCase would be removed from field arguments for queries:
```python
import strawberry


@strawberry.input
class Bar:
    a: str
    b: str
    some_values: list[str] | None = None


@strawberry.input(one_of=True)
class Foo:
    bar: strawberry.Maybe[Bar]
    c: strawberry.Maybe[str]


@strawberry.type
class Query:
    @strawberry.field
    async def foobar(
        self,
        info: strawberry.Info,
        foo: Foo = Foo(
            bar=strawberry.Some(Bar(a="hi", b="bye", some_values=["my", "world"])),
            c=None,
        ),
    ) -> str: ...


schema = strawberry.Schema(Query)
```

Once printed the output would look like the following with the some_values removed.
```graphql
directive @oneOf on INPUT_OBJECT

input Bar {
  a: String!
  b: String!
  someValues: [String!] = null
}

input Foo @oneOf {
  bar: Bar
  c: String
}

type Query {
  foobar(foo: Foo! = {bar: {a: "hi", b: "bye"}}): String!
}
```

After this fix, the value will be reflected in the print statement:
```graphql
directive @oneOf on INPUT_OBJECT

input Bar {
  a: String!
  b: String!
  someValues: [String!] = null
}

input Foo @oneOf {
  bar: Bar
  c: String
}

type Query {
  foobar(foo: Foo! = {bar: {a: "hi", b: "bye", someValues: ["my", "world"]}}): String!
}
```

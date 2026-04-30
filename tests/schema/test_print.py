import strawberry


def test_print_with_snake_case_values():

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

    assert schema.as_str() == \
"""directive @oneOf on INPUT_OBJECT

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
}"""


def test_print_with_camel_case_values():

    @strawberry.input
    class Bar:
        a: str
        b: str
        someValues: list[str] | None = None

    @strawberry.input(one_of=True)
    class Foo:
        bar: strawberry.Maybe[Bar]
        c: strawberry.Maybe[str]

    @strawberry.type
    class Query:
        @strawberry.field()
        async def foobar(
            self,
            info: strawberry.Info,
            foo: Foo = Foo(
                bar=strawberry.Some(Bar(a="hi", b="bye", someValues=["my", "world"])),
                c=None,
            ),
        ) -> str: ...

    schema = strawberry.Schema(Query)

    assert schema.as_str() == \
"""directive @oneOf on INPUT_OBJECT

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
}"""

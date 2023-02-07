Release type: minor

This release adds support for specialized generic types.
Before, the following code would give an error, saying that `T` was not
provided to the generic type:

```python
@strawberry.type
class Foo(Generic[T]):
    some_var: T


@strawberry.type
class IntFoo(Foo[int]):
    ...


@strawberry.type
class Query:
    int_foo: IntFoo
```

Also, because the type is already specialized, `Int` won't get inserted to its name,
meaning it will be exported to the schema with a type name of `IntFoo` and not
`IntIntFoo`.

For example, this query:

```python
@strawberry.type
class Query:
    int_foo: IntFoo
    str_foo: Foo[str]
```

Will generate a schema like this:

```graphql
type IntFoo {
  someVar: Int!
}

type StrFoo {
  someVar: String!
}

type Query {
  intFoo: IntFoo!
  strfoo: StrFoo!
}
```

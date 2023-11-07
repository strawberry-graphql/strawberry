Release type: minor

This release changes how we check for generic types. Previously, any type that
had a generic typevar would be considered generic for the GraphQL schema, this
would generate un-necessary types in some cases. Now, we only consider a type
generic if it has a typevar that is used as the type of a field or one of its arguments.

For example the following type:

```python
@strawberry.type
class Edge[T]:
    cursor: strawberry.ID
    some_interna_value: strawberry.Private[T]
```

Will not generate a generic type in the schema, as the typevar `T` is not used
as the type of a field or argument.

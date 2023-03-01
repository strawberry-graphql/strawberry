Release type: patch

This release covers an edge case where
```python
some_field: "Union[list[str], SomeType]]"
```
would not give a nice error.
Fixes [#2591](https://github.com/strawberry-graphql/strawberry/issues/2591)

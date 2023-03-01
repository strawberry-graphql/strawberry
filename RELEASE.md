Release type: patch

This release covers an edge case where the following would not give a nice error.
```python
some_field: "Union[list[str], SomeType]]"
Fixes [#2591](https://github.com/strawberry-graphql/strawberry/issues/2591)

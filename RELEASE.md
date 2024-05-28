Release type: patch

This release fixes an issue that would prevent using lazy aliased connections to
annotate a connection field.

For example, this should now work correctly:

```python
# types.py


@strawberry.type
class Fruit: ...


FruitConnection: TypeAlias = ListConnection[Fruit]
```

```python
# schema.py


@strawberry.type
class Query:
    fruits: Annotated["FruitConnection", strawberry.lazy("types")] = (
        strawberry.connection()
    )
```

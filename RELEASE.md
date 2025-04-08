Release type: minor

This releases improves support for `relay.Edge` subclasses.

`resolve_edge` now accepts `**kwargs`, so custom fields can be easily added to your edge classes:
```python
@strawberry.type(name="Edge", description="An edge in a connection.")
class CustomEdge(relay.Edge[NodeType]):
    index: int

    @classmethod
    def resolve_edge(
        cls, node: NodeType, *, cursor: Any = None, **kwargs: Any
    ) -> Self:
        assert isinstance(cursor, int)
        return super().resolve_edge(node, cursor=cursor, index=cursor, **kwargs)

```

You can also specify a custom cursor prefix, in case you want to implement a different
kind of cursor than a plain `ListConnection`:
```python
@strawberry.type(name="Edge", description="An edge in a connection.")
class CustomEdge(relay.Edge[NodeType]):
    CURSOR_PREFIX: ClassVar[str] = "mycursor"
```

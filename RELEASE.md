Release type: minor

This release adds support for returning interfaces directly in resolvers:

```python
@strawberry.interface
class Node:
    id: strawberry.ID

    @classmethod
    def resolve_type(cls, obj: Any, *args: Any, **kwargs: Any) -> str:
        return "Video" if obj.id == "1" else "Image"


@strawberry.type
class Video(Node):
    ...


@strawberry.type
class Image(Node):
    ...


@strawberry.type
class Query:
    @strawberry.field
    def node(self, id: strawberry.ID) -> Node:
        return Node(id=id)


schema = strawberry.Schema(query=Query, types=[Video, Image])
```

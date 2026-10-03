---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes types that inherit an
    interface, like relay.Node, through a base class that isn't decorated:
    the schema no longer fails with "can only implement Node once".
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes types that inherit an
    interface through a plain base class that isn't decorated with Strawberry,
    like a shared base for relay.Node types. Strawberry used to list the
    interface more than once, so building the schema failed; it's now listed
    once.
---

This release fixes types that inherit an interface through a class that isn't
decorated with Strawberry. Strawberry listed the interface more than once for
these types, so building the schema failed with errors like
`Type Fruit can only implement Node once.`

This happened, for example, when sharing `resolve_nodes` between `relay.Node`
types with a base class:

```python
import strawberry
from strawberry import relay


class DatabaseNode(relay.Node):
    @classmethod
    def resolve_nodes(cls, *, info, node_ids, required=False):
        return [load(cls, node_id) for node_id in node_ids]


@strawberry.type
class Fruit(DatabaseNode):
    id: relay.NodeID[int]
    name: str
```

`Fruit` now implements `Node` once. The same applies to interfaces that extend
another interface through an undecorated class, and the error raised when an
input inherits an interface this way now lists the interface once.

A class like `DatabaseNode` can share methods such as `resolve_nodes`, but
Strawberry ignores fields declared on it. To share fields too, decorate it with
`@strawberry.interface` or `@strawberry.type`.

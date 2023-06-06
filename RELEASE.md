Release type: patch

This release fixes an issue of the new relay integration adding an `id: GlobalID!`
argument on all objects that inherit from `relay.Node`. That should've only happened
for `Query` types.

Strawberry now will not force a `relay.Node` or any type that inherits it to be
inject the node extension which adds the argument and a resolver for it, meaning that
this code:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]


@strawberry.type
class Query:
    node: relay.Node
    fruit: Fruit
```

Should now be written as:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    id: relay.NodeID[int]


@strawberry.type
class Query:
    node: relay.Node = relay.node()  # <- note the "= relay.node()" here
    fruit: Fruit = relay.node()
```

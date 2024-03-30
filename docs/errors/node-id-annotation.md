---
title: Node ID annotation error
---

# Node `ID` annotation errors

## Description

This error is thrown when a `relay.Node` implemented type can't resolve its `id`
field, due to it being missing or multiple annotated fields being found.

The following code will throw this error:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    code: str
    name: str
```

This happens because `relay.Node` don't know which field should be used to
resolve to generate its `GlobalID` field.

The following would also throw this errors because multiple candidates were
found:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[str]
    name: relay.NodeID[str]
```

## How to fix this error

When inheriting from `relay.Node`, you should annotate exactly one `NodeID`
field in the type, like:

```python
import strawberry
from strawberry import relay


@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[str]
    name: str
```

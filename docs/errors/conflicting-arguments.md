---
title: Conflicting Arguments Error
---

# Conflicting Arguments Error

## Description

This error is thrown when you define a resolver with multiple arguments that
conflict with each other, like "self", "root", or any arguments annotated with
strawberry.Parent.

For example the following code will throw this error:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello(
        self, root, parent: strawberry.Parent[str]
    ) -> str:  #  <-- self, root, and parent all identify the same input
        return f"hello world"
```

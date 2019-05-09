Release Type: minor

Added support for declaring interface by using `@strawberry.interface`

Example:

```python
@strawberry.interface
class Node:
    id: strawberry.ID
```

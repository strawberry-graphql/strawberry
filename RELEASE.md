Release type: minor

This release adds the following scalar types:

- `JSON`
- `Base16`
- `Base32`
- `Base64`

they can be used like so:

```python
from strawberry.scalar import Base16, Base32, Base64, JSON

@strawberry.type
class Example:
    a: Base16
    b: Base32
    c: Base64
    d: JSON
```

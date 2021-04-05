Release type: minor

Add support for `default` and `default_factory` arguments in `strawberry.field`

```python
@strawberry.type
class Droid:
    name: str = strawberry.field(default="R2D2")
    aka: List[str] = strawberry.field(default_factory=["Artoo"])
```

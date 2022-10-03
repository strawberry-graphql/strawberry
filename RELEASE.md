Release type: patch

This release fixes the type of strawberry.federation.field,
this will prevent errors from mypy and pyright when doing the following:

```python
@strawberry.federation.type(keys=["id"])
class Location:
    id: strawberry.ID

    # the following field was reporting an error in mypy and pylance
    celestial_body: CelestialBody = strawberry.federation.field(
        resolver=resolve_celestial_body
    )
```

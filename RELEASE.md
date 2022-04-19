Release type: minor

Added support for deprecating Enum values with `deprecation_reason` while using `strawberry.enum_value` instead of string definition.

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = strawberry.enum_value("vanilla")
    STRAWBERRY = strawberry.enum_value(
        "strawberry", deprecation_reason="We ran out"
    )
    CHOCOLATE = "chocolate"
```

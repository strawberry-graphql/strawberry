Release type: minor

This release fixes a bug that was preventing the use of an enum member as the
default value for an argument.

For example:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
    PISTACHIO = "pistachio"

@strawberry.mutation
def create_flavour(
    self, flavour: IceCreamFlavour = IceCreamFlavour.STRAWBERRY
) -> str:
    return f"{flavour.name}"
```

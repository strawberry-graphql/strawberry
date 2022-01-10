Release type: patch

Improve typing of `@strawberry.enum()` by:

1. Using a `TypeVar` bound on `EnumMeta` instead of `EnumMeta`, which allows type-checkers (like pyright)
   to detect the fields of the enum being decorated. For example, for the following enum:

```python
@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"
```

   Prior to this change, pyright would complain if you tried to access
   `IceCreamFlavour.VANILLA`, since the type information of `IceCreamFlavour` was being
   erased by the `EnumMeta` typing  .

2. Overloading it so that type-checkers (like pyright) knows in what cases it returns a decorator
   (when it's called with keyword arguments, e.g. `@strawberry.enum(name="IceCreamFlavor")`),
   versus when it returns the original enum type (without keyword arguments.

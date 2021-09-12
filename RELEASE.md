Release type: patch

Fix issues ([#1158][issue1158] and [#1104][issue1104]) where Generics using LazyTypes
and Enums would not be properly resolved

These now function as expected:

# Enum

```python
T = TypeVar("T")

@strawberry.enum
class VehicleMake(Enum):
    FORD = 'ford'
    TOYOTA = 'toyota'
    HONDA = 'honda'

@strawberry.type
class GenericForEnum(Generic[T]):
    generic_slot: T

@strawberry.type
class SomeType:
    field: GenericForEnum[VehicleMake]
```

# LazyType

`another_file.py`
```python
@strawberry.type
class TypeFromAnotherFile:
    something: bool
```

`this_file.py`
```python
T = TypeVar("T")

@strawberry.type
class GenericType(Generic[T]):
    item: T

@strawberry.type
class RealType:
    lazy: GenericType[LazyType["TypeFromAnotherFile", "another_file.py"]]
```

[issue1104]: https://github.com/strawberry-graphql/strawberry/issues/1104
[issue1158]: https://github.com/strawberry-graphql/strawberry/issues/1158

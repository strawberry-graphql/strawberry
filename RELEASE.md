Release type: patch

Fix issue ([#1158][issue]) where Generics using LazyTypes would not be properly resolved

This now functions as expected:

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

[issue]: https://github.com/strawberry-graphql/strawberry/issues/1158

Release type: minor

Previously, `strawberry.field` had redundant arguments for the resolver, one for
when `strawberry.field` was used as a decorator, and one for when it was used as
a function. These are now combined into a single argument.

The `f` argument of `strawberry.field` no longer exists. This is a
backwards-incompatible change, but should not affect many users. The `f` 
argument was the first argument for `strawberry.field` and its use was only
documented without the keyword. The fix is very straight-forward: replace any 
`f=` kwarg with `resolver=`.

```python
@strawberry.type
class Query:
    
    my_int: int = strawberry.field(f=lambda: 5)
    # becomes
    my_int: int = strawberry.field(resolver=lambda: 5)

    # no change
    @strawberry.field
    def my_float(self) -> float:
        return 5.5

```

Other (minor) breaking changes
* `MissingArgumentsAnnotationsError`'s message now uses the original Python
field name instead of the GraphQL field name. The error can only be thrown while
instantiating a strawberry.field, so the Python field name should be more
helpful.
* As a result, `strawberry.arguments.get_arguments_from_resolver()` now only
takes one field -- the `resolver` Callable.
* `MissingFieldAnnotationError` is now thrown when a strawberry.field is not
type-annotated but also has no resolver to determine its type

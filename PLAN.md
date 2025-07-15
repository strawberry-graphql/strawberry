Plan to add first class support for Pydantic, similar to how it was outlined here:

https://github.com/strawberry-graphql/strawberry/issues/2181

Note:

We have already support for pydantic, but it is experimental, and works like this:

```python
class UserModel(BaseModel):
    age: int

@strawberry.experimental.pydantic.type(
    UserModel, all_fields=True
)
class User: ...
```

The issue is that we need to create a new class that for the GraphQL type,
it would be nice to remove this requirement and do this instead:

```python
@strawberry.pydantic.type
class UserModel(BaseModel):
    age: int
```

This means we can directly pass a pydantic model to the strawberry pydantic type decorator.

The implementation should be similar to `strawberry.type` implement in strawberry/types/object_type.py,
but without the dataclass work.

The current experimental implementation can stay there, we don't need any backward compatibility, and
we also need to support the latest version of pydantic (v2+).

We also need support for Input types, but we can do that in a future step.

Release type: minor

This release adds a new utility function to convert a Strawberry object to a
dictionary.

You can use `strawberry.asdict(...)` function to convert a Strawberry object to
a dictionary:

```python
@strawberry.type
class User:
    name: str
    age: int


# should be {"name": "Lorem", "age": 25}
user_dict = strawberry.asdict(User(name="Lorem", age=25))
```

> Note: This function uses the `dataclasses.asdict` function under the hood, so
> you can safely replace `dataclasses.asdict` with `strawberry.asdict` in your
> code. This will make it easier to update your code to newer versions of
> Strawberry if we decide to change the implementation.

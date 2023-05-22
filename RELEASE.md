Release type: minor

This release introduces the new `should_ignore` argument to the `QueryDepthLimiter` extension that provides
a more general and more verbose way of specifying the rules by which a query's depth should be limited.

The `should_ignore` argument should be a function that accepts a single argument of type `IgnoreContext`.
The `IgnoreContext` class has the following attributes:
- `field_name` of type `str`: the name of the field to be compared against
- `field_args` of type `strawberry.extensions.query_depth_limiter.FieldArgumentsType`: the arguments of the field to be compared against
- `query` of type `graphql.language.Node`: the query string
- `context` of type `graphql.validation.ValidationContext`: the context passed to the query
and returns `True` if the field should be ignored and `False` otherwise.
This argument is injected, regardless of name, by the `QueryDepthLimiter` class and should not be passed by the user.

Instead, the user should write business logic to determine whether a field should be ignored or not by
the attributes of the `IgnoreContext` class.

For example, the following query:
```python
"""
    query {
      matt: user(name: "matt") {
        email
      }
      andy: user(name: "andy") {
        email
        address {
          city
        }
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```
can have its depth limited by the following `should_ignore`:
```python
from strawberry.extensions import IgnoreContext


def should_ignore(ignore: IgnoreContext):
    return ignore.field_args.get("name") == "matt"


query_depth_limiter = QueryDepthLimiter(should_ignore=should_ignore)
```
so that it *effectively* becomes:
```python
"""
    query {
      andy: user(name: "andy") {
        email
        pets {
          name
          owner {
            name
          }
        }
      }
    }
"""
```

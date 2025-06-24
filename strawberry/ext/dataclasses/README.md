# Additional information

This folder contains file(s) or code that is originally taken from other
projects and got further adaptations by the maintainers of Strawberry.

## `dataclasses.py`

The file
[dataclasses.py](https://github.com/strawberry-graphql/strawberry/tree/main/strawberry/ext/dataclasses/dataclasses.py)
which is based on
https://github.com/python/cpython/blob/v3.9.6/Lib/dataclasses.py#L489-L536
but has got some small adjustments in the adopted function
`dataclass_init_fn()` so the functionality is fitting the desired
requirements within Strawberry.

From the docstring of `dataclass_init_fn()`:

```
"""
Create an __init__ function for a dataclass.

We create a custom __init__ function for the dataclasses that back
Strawberry object types to only accept keyword arguments. This allows us to
avoid the problem where a type cannot define a field with a default value
before a field that doesn't have a default value.

An example of the problem:
https://stackoverflow.com/questions/51575931/class-inheritance-in-python-3-7-dataclasses

Code is adapted from:
https://github.com/python/cpython/blob/v3.9.6/Lib/dataclasses.py#L489-L536

Note: in Python 3.10 and above we use the `kw_only` argument to achieve the
same result.
"""
```

The file was added so kwargs could be enforced on Python classes within
Strawberry.
See also the file LICENSE for copyright information.

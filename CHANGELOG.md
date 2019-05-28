CHANGELOG
=========

0.10.0 - 2019-05-28
-------------------

Fixed issue that was prevent usage of InitVars.
Now you can safely use InitVar to prevent fields from showing up in the schema:


```python
@strawberry.type
class Category:
    name: str
    id: InitVar[str]

@strawberry.type
class Query:
    @strawberry.field
    def category(self, info) -> Category:
        return Category(name="example", id="123")
```

0.9.1 - 2019-05-25
------------------

Fixed logo on PyPI

0.9.0 - 2019-05-24
------------------

Added support for passing resolver functions

```python
def resolver(root, info, par: str) -> str:
    return f"hello {par}"

@strawberry.type
class Query:
    example: str = strawberry.field(resolver=resolver)
```

Also we updated some of the dependencies of the project

0.8.0 - 2019-05-09
------------------

Added support for renaming fields. Example usage:
```python
@strawberry.type
class Query:
example: str = strawberry.field(name='test')
```

0.7.0 - 2019-05-09
------------------

Added support for declaring interface by using `@strawberry.interface`
Example:
```python
@strawberry.interface
class Node:
id: strawberry.ID
```

0.6.0 - 2019-05-02
------------------

This changes field to be lazy by default, allowing to use circular dependencies
when declaring types.

0.5.6 - 2019-04-30
------------------

Improve listing on pypi.org

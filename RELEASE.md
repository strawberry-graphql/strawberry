Release type: minor

Starting with this release, Strawberry will throw an error if one of your input
types tries to inherit from one or more interfaces. This new error enforces the
GraphQL specification that input types cannot implement interfaces.

The following code, for example, will now throw an error:

```python
import strawberry


@strawberry.interface
class SomeInterface:
    some_field: str


@strawberry.input
class SomeInput(SomeInterface):
    another_field: int
```

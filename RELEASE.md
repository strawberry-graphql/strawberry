Release type: minor

This PR allows passing metadata to Strawberry arguments.

Example:

```python
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def hello(
        self,
        info,
        input: Annotated[str, strawberry.argument(metadata={"test": "foo"})],
    ) -> str:
        argument_definition = info.get_argument_definition("input")
        assert argument_definition.metadata["test"] == "foo"

        return f"Hi {input}"
```

Release type: patch

Add `get_argument_definition` helper function on the Info object to get
a StrawberryArgument definition by argument name from inside a resolver or
Field Extension.

Example:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def field(
        self,
        info,
        my_input: Annotated[
            str,
            strawberry.argument(description="Some description"),
        ],
    ) -> str:
        my_input_def = info.get_argument_definition("my_input")
        assert my_input_def.type is str
        assert my_input_def.description == "Some description"

        return my_input
```

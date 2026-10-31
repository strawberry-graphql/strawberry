---
release type: patch
---

This release fixes the name and description of enums registered with
`Annotated` when they're used as resolver arguments:

```python
class Color(Enum):
    RED = "red"


GqlColor = Annotated[Color, strawberry.enum(name="GqlColor", description="A color")]


@strawberry.type
class Query:
    @strawberry.field
    def color_name(self, color: GqlColor) -> str:  # was `Color!`, now `GqlColor!`
        return color.value
```

Strawberry removed all the `Annotated` metadata from arguments annotated
directly with the alias, or with
`Annotated[GqlColor, strawberry.argument(...)]`, not only
`strawberry.argument()`. The enum was then registered with the name of the
Python class, and since an enum is only registered once, this also renamed it
in the rest of the schema whenever such an argument was defined before the
other uses of the alias.

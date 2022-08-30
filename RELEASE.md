Release type: patch

This release adds support for passing schema directives to
`Schema(..., types=[])`. This can be useful if using a built-inschema directive
that's not supported by a gateway.

For example the following:

```python
import strawberry
from strawberry.scalars import JSON
from strawberry.schema_directive import Location


@strawberry.type
class Query:
    example: JSON


@strawberry.schema_directive(locations=[Location.SCALAR], name="specifiedBy")
class SpecifiedBy:
    name: str


schema = strawberry.Schema(query=Query, types=[SpecifiedBy])
```

will print the following SDL:

```graphql
directive @specifiedBy(name: String!) on SCALAR

"""
The `JSON` scalar type represents JSON values as specified by [ECMA-404](http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf).
"""
scalar JSON
  @specifiedBy(
    url: "http://www.ecma-international.org/publications/files/ECMA-ST/ECMA-404.pdf"
  )

type Query {
  example: JSON!
}
```

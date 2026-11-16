---
release type: minor
---

This release adds expected-type validation for `GlobalID` arguments. You can
now declare the type (or types) a `GlobalID` argument must refer to via
`Annotated` metadata, and Strawberry validates incoming IDs during argument
coercion:

```python
@strawberry.type
class Query:
    @strawberry.field
    def user(self, user_id: Annotated[GlobalID, User]) -> str: ...

    @strawberry.field
    def member(self, member_id: Annotated[GlobalID, User, Team]) -> str: ...
```

A `GlobalID` whose type name does not match is rejected with an
`InvalidGlobalIDError` input error. Lazy references are supported via
`Annotated[GlobalID, Annotated["User", strawberry.lazy("...")]]`. Non-type
`Annotated` metadata (plain strings, arbitrary objects) keeps its previous
meaning and is ignored, while type expectations in unsupported placements
(inside lists, tuples, deeper unions, on container annotations, or on
input-object fields) raise a clear `TypeError` at schema build time instead
of being silently ignored.

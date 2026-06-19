Release type: minor

Add support for GraphQL object and input object type extensions.

`@strawberry.type(..., extend=True)` and `@strawberry.input(..., extend=True)`
can now be registered alongside a base type with the same GraphQL name. The
generated SDL prints extension definitions as `extend type` and `extend input`,
and input extension fields are available on converted resolver arguments.

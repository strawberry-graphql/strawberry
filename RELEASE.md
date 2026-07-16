---
release type: patch
social_messages:
  x: >-
    🍓 Strawberry {version} is out! This release fixes a crash when printing a
    schema whose custom-scalar (e.g. JSON) input default is a list.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    Strawberry {version} is out. This release fixes a crash when printing a
    schema whose custom-scalar (e.g. JSON) input default is or contains a list,
    so SDL export and snapshot tests keep working for list-valued defaults.
---

This release fixes a crash when printing a schema whose custom-scalar (e.g.
`JSON`) input field has a list-valued default.

`ast_from_leaf_type` handled `dict`/`str`/number defaults but had no branch for
lists, so a field like
`j: JSON = strawberry.field(default_factory=lambda: [1, 2, 3])` — or a list
nested inside a dict default — raised `TypeError: Cannot convert value to AST`
when the schema was printed. Lists (and tuples) are now converted correctly.

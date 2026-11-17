---
release type: patch
---

This release fixes query codegen for input fields whose default value is a
renamed enum member.

Defaults were printed with the Python names of the enum and its member (for
example `Order.DESCENDING`), while the generated enum is built from the GraphQL
names declared with `strawberry.enum(name=...)` and
`strawberry.enum_value(name=...)`. The generated Python module then failed to
import. Defaults now use the GraphQL names (for example `SortOrder.DESC`).

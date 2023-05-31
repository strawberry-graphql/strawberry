Release type: patch

codegen no longer chokes on queries that have a `__typename` in them.
Python generated types will not have the `__typename` included in the fields.

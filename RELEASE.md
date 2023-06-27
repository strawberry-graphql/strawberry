Release type: minor

This release refactors the way we resolve field types to to make it
more robust, resolving some corner cases.

One case that should be fixed is when using specialized generics
with future annotations.

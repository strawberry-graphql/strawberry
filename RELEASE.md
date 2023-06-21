Release type: patch

This release removes `get_object_definition_strict` and instead
overloads `get_object_definition` to accept an extra `strct` keyword.

This is a new feature so it is unlikely to break anything.

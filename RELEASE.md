Release type: patch

This release fixes a regression introduced in version 0.118.2 which
could make the check to see if a type is instance of auto raise
`NameError` when that type is a subclass of `StrawberryType`.

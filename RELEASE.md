Release type: patch

This release fixes a typing regression on `StraberryContainer` subclasses
where type checkers would not allow non `WithStrawberryObjectDefinition` types
to be passed for its `of_type` argument (e.g. `StrawberryOptional(str)`)

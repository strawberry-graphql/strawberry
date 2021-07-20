Release type: minor

Refactor of the library's typing internals. Previously, typing was handled
individually by fields, arguments, and objects with a hodgepodge of functions to tie it
together. This change creates a unified typing system that the object, fields, and
arguments each hook into.

Mainly replaces the attributes that were stored on StrawberryArgument and
StrawberryField with a hierarchy of StrawberryTypes.

Introduces `StrawberryAnnotation`, as well as `StrawberryType` and some subclasses,
including `StrawberryList`, `StrawberryOptional`, and `StrawberryTypeVar`.

This is a breaking change if you were calling the constructor for `StrawberryField`,
`StrawberryArgument`, etc. and using arguments such as `is_optional` or `child`.

`@strawberry.field` no longer takes an argument called `type_`. It instead takes a
`StrawberryAnnotation` called `type_annotation`.

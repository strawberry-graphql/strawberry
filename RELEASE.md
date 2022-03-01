Release type: minor

Change `strawberry.auto` to be a type instead of a sentinel.
This not only removes the dependency on sentinel from the project, but also fixes
some related issues, like the fact that only types can be used with `Annotated`.

Also, custom scalars will now trick static type checkers into thinking they
returned their wrapped type. This should fix issues with pyright 1.1.224+ where
it doesn't allow non-type objects to be used as annotations for dataclasses and
dataclass-alike classes (which is strawberry's case). The change to `strawberry.auto`
also fixes this issue for it.

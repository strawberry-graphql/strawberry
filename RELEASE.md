Release type: patch

Correct a type-hinting bug with `strawberry.directive`.
This may cause some consumers to have to remove a `# type: ignore` comment
or unnecessary `typing.cast` in order to get `mypy` to pass.

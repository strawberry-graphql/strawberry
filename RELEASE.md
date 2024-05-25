Release type: minor

When calling the CLI without all the necessary dependencies installed,
a `MissingOptionalDependenciesError` will be raised instead of a
`ModuleNotFoundError`. This new exception will provide a more helpful
hint regarding how to fix the problem.

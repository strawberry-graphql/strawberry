Release type: patch

This release fixes a bug where using a custom scalar in a union would result
in an unclear exception. Instead, when using a custom scalar in a union,
the `InvalidUnionType` exception is raised with a clear message that you
cannot use that type in a union.

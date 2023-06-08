Release type: patch

This release fixes a bug where codegen would fail on mutations that have object arguments in the query.

Additionally, it does a topological sort of the types before passing it to the plugins to ensure that
dependent types are defined after their dependencies.

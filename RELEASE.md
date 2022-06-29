Release type: minor

New `Lazy` that will replace `LazyType` in the future. It is aliased to
`LazyType` at runtime, but static type checkers (e.g. pyright) see them as
`Annotated`. That means that using it will prevent typing issues and also
make those same static type checkers to properly type them.

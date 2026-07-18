Release type: patch

Document how to use ordinary Python types with the `JSON` scalar via
`graphql_type`, addressing the lack of usage guidance reported in #4092.
Covers both resolver return values and input arguments. Add typechecker and
runtime regression tests guarding the workaround across mypy, pyright, and ty;
the `JSON(value)` constructor contract; the runtime identity serialize/parse
behaviour; and that `scalar_map`/`scalar_overrides` for JSON are respected.

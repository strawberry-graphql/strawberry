Release type: patch

Fixed a bug where using `relay.node()` or `relay.connection()` would raise a
`DeprecationWarning` about "Argument name-based matching of 'info'", even though
the `info` parameter was correctly annotated.

This also fixes the same warning when using Python 3.12+ type alias syntax for
`Info`, such as `type MyInfo = strawberry.Info[Context, None]`.

The fix recognizes `strawberry.Info` and `strawberry.Parent` annotations (with
or without generic parameters) when they appear as string forward references.
Only fully qualified names are matched to avoid confusion with user-defined types.

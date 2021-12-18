Release type: patch

Change `context_getter` in `strawberry.fastapi.GraphQLRouter` to merge, rather than overwrite, default and custom getters.

This mean now you can always access the `request` instance from `info.context`, even when using
a custom context getter.

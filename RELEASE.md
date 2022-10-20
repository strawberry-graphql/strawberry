Release type: minor

This release refactors the chalice integration in order to keep it consistent with
the other integrations.

## Deprecation

Passing `render_graphiql` is now deprecated, please use `graphiql` instead.

## New features

- You can now return a custom status by using `info.context["response"].status_code = 418`
- You can enabled/disable queries via get using `allow_queries_via_get` (defaults to `True`)

## Changes

Trying to access /graphql via a browser and with `graphiql` set to `False` will return a 404.

Release type: minor

In this release, we renamed the `strawberry server` command to `strawberry dev`
to better reflect its purpose as a development server.

Note, that we also renamed the `strawberry[debug-server]` extra to
`strawberry[dev-server]`. The old extra name is still supported but will be
removed in a future release. We recommend to update dependencies accordingly.

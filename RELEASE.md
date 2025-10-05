Release type: minor

In this release, we renamed the `strawberry server` command to `strawberry dev`
to better reflect its purpose as a development server.

We also deprecated the `strawberry-graphql[debug-server]` extra in favor of
`strawberry-graphql[cli]`. Please update your dependencies accordingly.

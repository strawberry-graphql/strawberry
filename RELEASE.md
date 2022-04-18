Release type: minor

This release adds support in all our integration for queries via GET requests.
This behavior is enabled by default, but you can disable it by passing
`allow_queries_via_get=False` to the constructor of the integration of your
choice.

For security reason only queries are allowed via `GET` requests.

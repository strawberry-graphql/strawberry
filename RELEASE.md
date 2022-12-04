Release type: minor

This release updates the Sanic integration and includes some breaking changes.
You might need to update your code if you are customizing `get_context` or
`process_result`

`get_context` now receives the request as the first argument and the response as
the second argument.

`process_result` is now async and receives the request and the GraphQL execution
result.

This change is needed to align all the HTTP integrations and reduce the amount
of code needed to maintain. It also makes the errors consistent with other
integrations.

It also brings a new feature and it allows to customize the HTTP status code by
using `info.context["response"].status_code = YOUR_CODE`.

It also removes the upper bound on the Sanic version, so you can use the latest
version of Sanic with Strawberry.

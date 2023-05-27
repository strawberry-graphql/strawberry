Release type: minor

This release updates the Django Channels integration so that it uses the same base
classes used by all other integrations.

**New features:**

The Django Channels integration supports two new features:

* Setting headers in the response
* File uploads via `multipart/form-data` POST requests

**Breaking changes:**

This release contains a breaking change for the Channels integration. The context
object is now a `dict` and it contains different keys depending on the connection
protocol:

1. HTTP: `request` and `response`. The `request` object contains the full
   request (including the body). Previously, `request` was a `GraphQLHTTPConsumer`
   instance of the current connection. The consumer is now available via
   `request.consumer`.
2. WebSockets: `request`, `ws` and `response`. `request` and `ws` are the same
   `GraphQLWSConsumer` instance of the current connection.

If you want to use a dataclass for the context object (like in previous releases),
you can still use them by overriding the `get_context` methods. See the Channels
integration documentation for an example.

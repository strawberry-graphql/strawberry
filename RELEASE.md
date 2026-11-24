---
release type: patch
---

This release fixes how the WebSocket protocol handlers deal with messages that
are valid JSON but not valid protocol messages.

Previously, a message that wasn't a JSON object (such as `[]`, `"hello"`, `1` or
`null`), or a `subscribe`/`start` message whose `id` or `payload` had the wrong
type (for example `{"type": "subscribe", "id": "1", "payload": "{ hello }"}`),
raised an unhandled `TypeError` in the handler. The connection was torn down
with a server error instead of the close code defined by the protocol, and the
exception was logged by the web framework as an internal error.

Now:

- `graphql-transport-ws` closes the connection with `4400: Failed to parse
  message`, as it already did for messages missing a required field. This
  applies to non-object messages, to `subscribe` messages whose `id` isn't a
  string, whose `payload` isn't an object, whose `query` isn't a string, or
  whose `variables`/`operationName` have the wrong type, and to `complete`
  messages whose `id` isn't a string.
- The legacy `graphql-ws` protocol ignores these messages, in the same way it
  already ignores messages that aren't valid JSON or have an unknown type. This
  also covers messages without a `type`, `start` messages without an `id`,
  `payload` or `query`, and `stop` messages without an `id`, which used to
  raise a `KeyError`.

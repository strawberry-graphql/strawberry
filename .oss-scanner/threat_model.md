# Threat model

## What this project does and where untrusted input enters

Strawberry is a Python library for building GraphQL servers. Developers define a schema with decorators
(`@strawberry.type`, `@strawberry.field`, ...) and serve it through one of the bundled integrations (ASGI, Django,
Channels, FastAPI, Flask, Quart, Sanic, aiohttp, Litestar, Chalice). The schema itself is written by the developer and
is trusted. Everything a client sends is untrusted:

- HTTP requests to the GraphQL view (`strawberry/http/async_base_view.py`, `sync_base_view.py`, `base.py`): the JSON
  body, the query string for GET requests, headers (content type, `Accept`), multipart file uploads
  (`strawberry/file_uploads/`, only when `multipart_uploads_enabled=True`) and batched requests (when `batching_config`
  is set).
- The GraphQL document, variables, operation name and extensions. Parsing and validation are done by graphql-core;
  Strawberry adds its own execution (`strawberry/schema/`), argument and input conversion (`strawberry/types/arguments.py`
  and friends), scalars (`strawberry/scalars.py`, `strawberry/types/` date/time/decimal/UUID/JSON/Base64 scalars) and
  enum handling.
- WebSocket messages for subscriptions: `graphql-transport-ws` and the legacy `graphql-ws` protocol
  (`strawberry/subscriptions/protocols/`), including `connection_init` payloads used for authentication, and the
  Channels consumers (`strawberry/channels/`).
- Streaming HTTP responses: `@defer`/`@stream` over `multipart/mixed`, subscriptions over multipart and SSE
  (`strawberry/http/streaming.py`).
- Relay global IDs and connection pagination arguments (`strawberry/relay/`): IDs are base64 strings that clients can
  forge, and `first`/`last`/`before`/`after` are client controlled.
- Federation entity resolution (`strawberry/federation/`): `_entities` representations and `_service { sdl }`.

Developer-facing tooling also handles input that may not be trusted in practice: `strawberry codegen` (generates
client code from GraphQL queries and a schema) and `strawberry schema-codegen` (generates Python from GraphQL SDL).
Generated code that lets crafted input inject Python or TypeScript is in scope.

## Components that matter most / least

Most:

- Security controls that applications rely on: permission classes (`strawberry/permission.py`), including sync vs
  async permission results; `DisableIntrospection`, `MaskErrors`, `QueryDepthLimiter`, `MaxTokensLimiter`,
  `MaxAliasesLimiter` and `AddValidationRules` in `strawberry/extensions/`. A way to bypass any of these is the most
  valuable class of finding.
- The HTTP views: CSRF protection (mutations over GET, content types that avoid CORS preflight), request size and batch
  limits, multipart upload parsing, content negotiation, and error responses that leak internals.
- Subscription protocols: authentication via `connection_init`, per-connection limits on operations, cleanup of
  completed or cancelled operations, and anything that lets one client starve the server.
- Relay node resolution and pagination: resolving a global ID to the wrong type, or pagination that walks unbounded
  data.
- Type resolution for interfaces and unions (returning data typed as something the client should not see).

Least:

- GraphiQL / Apollo Sandbox HTML (`strawberry/static/`) beyond XSS or leaking credentials.
- `strawberry/codemods/`, `strawberry/ext/mypy_plugin.py` and other developer-only tooling that only reads the
  developer's own source code.
- `docs/`, `tests/` and the benchmarks (`tests/benchmarks/`) are out of scope.

## How to exercise it

- `tests/` is the pytest suite. `tests/http/` runs the same HTTP tests against every integration through clients in
  `tests/http/clients/`; `tests/websockets/` does the same for both subscription protocols. These are the fastest way
  to build a reproducer: add a test that uses the `http_client` fixture so it runs on all integrations.
- Run tests with `python -m pytest tests/http -q -n auto` (the venv is already on PATH).
- `strawberry.Schema(...).execute_sync(query)` / `await schema.execute(query)` runs a query without any web framework.
- `strawberry server <module>:schema` starts a development server with uvicorn.

## How you rate severity

- Critical: unauthenticated remote code execution, or a bypass of authentication/permissions that exposes or modifies
  data in a default or common configuration.
- High: bypass of a permission class or of a security extension (`DisableIntrospection`, `MaskErrors`, query limiters)
  in a realistic configuration; authentication bypass on a subscription transport; code injection through
  `schema-codegen` or `codegen` from attacker-controlled input; denial of service where a single small request makes
  the server use unbounded memory or CPU, or blocks the event loop, when the documented limits are configured.
- Medium: denial of service that needs sustained traffic or many connections, or only affects a non-default feature;
  CSRF; information disclosure of stack traces or internal type names when masking is enabled.
- Low: issues that need an unusual configuration or a developer mistake that the docs already warn about; minor
  information leaks; hardening suggestions.

Resource exhaustion through an expensive query on an application that has not configured any of the query limiting
extensions is expected behavior, not a vulnerability, unless the cost is out of proportion with the query (for
example, exponential work from a small document).

## Anything to leave alone

- Bugs in graphql-core, the web frameworks or other dependencies, unless Strawberry uses them in an unsafe way. Report
  them only if Strawberry is the right place for the fix.
- Introspection being enabled, GraphiQL being served, or query batching being accepted when the developer turned these
  on (or did not turn them off). These are documented configuration choices.
- Vulnerabilities in resolvers written by the application developer.

## Reports and patches

Please include a pytest test that reproduces the issue (ideally under `tests/http/` or `tests/websockets/` so it runs
against every integration) and a patch that keeps both the sync and async execution paths working.

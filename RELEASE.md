Release type: minor

Add SSE `connection_params` mirroring and `on_sse_connect` to drop SSE connections at the transport level.

SSE subscriptions mirror the `Authorization` header into `context["connection_params"]["authorization"]`, matching WebSocket behaviour. Override `on_sse_connect` to accept or reject connections at the transport level. Before now, there was no equivalent to `on_ws_connect` for SSE — the only way to reject an unauthorized connection was to throw inside the subscription resolver after the stream had already started.

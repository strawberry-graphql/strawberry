Release type: patch

Await cancelled subscription tasks during WebSocket shutdown so their `finally` blocks run before shared state (DB pools, event loop) is torn down.

Release type: patch

This release fixes the issue that some coroutines in the WebSocket protocol handlers were never awaited if clients disconnected shortly after starting an operation.

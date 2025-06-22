Release type: patch

In this release, we updated the `aiohttp` integration to handle
`aiohttp.ClientConnectionResetError`s, which can occur when a WebSocket
connection is unexpectedly closed, gracefully.

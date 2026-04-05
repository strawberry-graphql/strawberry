Release type: patch

Fix a memory leak in the `graphql-transport-ws` WebSocket handler where completed
task objects would accumulate in a list between messages. Task cleanup now uses
`asyncio.Task.add_done_callback` for immediate cleanup instead of deferred reaping.

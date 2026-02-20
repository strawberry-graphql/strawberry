Release type: patch

Fix `execution_context.result` being `None` or belonging to a wrong request when multiple async requests execute concurrently (e.g. via `asyncio.gather`). Shared cached extension instances are no longer reused across concurrent async requests.

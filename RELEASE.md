release type: patch

This release fixes that the ASGI subscription implementation did not handle
disconnecting clients properly. Additionally, the ASGI implementation has been
internally refactored to match the AIOHTTP implementation.

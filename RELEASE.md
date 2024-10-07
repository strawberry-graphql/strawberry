Release type: minor

The AIOHTTP, ASGI, and Django test clients' `asserts_errors` option has been renamed to `assert_no_errors` to better reflect its purpose.
This change is backwards-compatible, but the old option name will raise a deprecation warning.

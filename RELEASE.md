Release type: minor

This release updates all\* the HTTP integration to use the same base class,
which makes it easier to maintain and extend them in future releases.

While this doesn't provide any new features (other than settings headers in
Chalice and Sanic), it does make it easier to extend the HTTP integrations in
the future. So, expect some new features in the next releases!

**New features:**

Now both Chalice and Sanic integrations support setting headers in the response.
Bringing them to the same level as the other HTTP integrations.

**Breaking changes:**

Unfortunately, this release does contain some breaking changes, but they are
minimal and should be quick to fix.

1. Flask `get_root_value` and `get_context` now receive the request
2. Sanic `get_root_value` now receives the request and it is async

\* The only exception is the channels http integration, which will be updated in
a future release.

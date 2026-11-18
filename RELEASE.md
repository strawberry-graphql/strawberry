---
release type: patch
---

This release fixes the Pydantic field-extension default test by removing its
stale expected-failure marker and updating its field-order assertion to the
current behaviour. Default values have worked since the original issue was
fixed; no library behaviour changes.

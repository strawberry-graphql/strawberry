---
release type: patch
---

Remove the stale expected-failure marker from the pydantic field-extension
default test: default values have worked since the original issue was fixed,
and the test's field-order assertion is updated to the current behaviour.

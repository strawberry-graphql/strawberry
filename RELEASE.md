---
release type: patch
---

This release fixes an issue in the bundled GraphiQL template where editing HTTP
headers, including `Authorization` headers, wrote those values into the browser
URL.

GraphiQL still supports loading headers from existing `headers` URL parameters,
but newly edited headers are no longer added to the URL. Query and variables URL
sharing is unchanged.

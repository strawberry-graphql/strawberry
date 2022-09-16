Release type: patch

Fix warnings during unit tests for Sanic's upload.

Otherwise running unit tests results in a bunch of warning like this:

```
DeprecationWarning: Use 'content=<...>' to upload raw bytes/text content.
```

Release type: patch

This release fixes an issue with the http multipart subscription where the
status code would be returned as `None`, instead of 200.

We also took the opportunity to update the internals to better support
additional protocols in future.

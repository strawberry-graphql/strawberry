---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Non-string variables for UUID, Date,
    DateTime and Time now return a clean coercion error instead of a server
    error. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Non-string variables for the built-in
    UUID, Date, DateTime and Time scalars now return a clean coercion error
    rather than surfacing as a server error in your error tracker.
---

This release fixes non-string variables for the built-in `UUID`, `Date`,
`DateTime` and `Time` scalars being reported as server errors.

These parsers accept only strings and raise `AttributeError` or `TypeError` on
anything else, which escaped the scalar wrapper and reached the client as the
standard library's own message, such as `'float' object has no attribute
'replace'`. Error trackers then recorded plain invalid input as a crash
fingerprinted on stdlib frames.

Values are now coerced with `str()` before parsing, the same way `Decimal`
already did, so an unparseable value raises a `ValueError` that the wrapper
reports as a normal coercion error.

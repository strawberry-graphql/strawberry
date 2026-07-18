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

A non-string value is now reported as an ordinary coercion error:

```
Value cannot represent a UUID: "469610.0".
```

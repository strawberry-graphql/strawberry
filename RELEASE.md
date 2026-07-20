---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes the built-in UUID,
    Date, DateTime and Time scalars to reject non-string values with a proper
    coercion error instead of crashing with an unhandled exception. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. The built-in UUID, Date, DateTime and
    Time scalars now reject non-string variable values with a standard GraphQL
    coercion error instead of raising an unhandled AttributeError or
    TypeError, keeping plain bad client input out of server-side error
    tracking.
---

This release fixes the built-in `UUID`, `Date`, `DateTime`, and `Time` scalars
to reject non-string variable values with a standard coercion error instead of
raising an unhandled `AttributeError`/`TypeError` inside the parser.

Previously a value like `{"id": 469610.0}` sent into a `UUID` position crashed
with `'float' object has no attribute 'replace'` and surfaced in error
trackers as a server-side exception. The `Decimal` scalar keeps accepting
numeric input by stringifying it, as before.

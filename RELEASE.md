Release type: patch

The built-in `UUID`, `Date`, `DateTime`, and `Time` scalars now reject non-string variable values with a standard coercion error, matching the existing `Decimal` behavior, instead of raising an unhandled `AttributeError`/`TypeError` inside the parser. Previously a value like `{"id": 469610.0}` sent into a `UUID` position crashed with `'float' object has no attribute 'replace'` and surfaced in error trackers as a server-side exception.

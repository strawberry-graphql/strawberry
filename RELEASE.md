---
release type: patch
---

This release fixes `strawberry schema-codegen` generating invalid Python for
strings that need escaping.

Descriptions, `@specifiedBy` URLs, directive arguments and string default
values containing both kinds of quotes, backslashes or control characters are
now escaped correctly, so they keep their content in the generated code.

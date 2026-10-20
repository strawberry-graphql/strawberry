---
release type: patch
---

This release fixes `strawberry schema-codegen` adding a newline to the start and
end of multi-line descriptions.

Multi-line strings are still written as triple-quoted strings on their own
lines, but the generated code now uses escaped line breaks so the description
matches the one in the schema exactly.

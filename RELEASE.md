Release type: minor

This release fixes an issue where field extensions were being applied multiple times when a field was used in multiple schemas. This could lead to unexpected behavior or errors if the extension's `apply` method wasn't idempotent.

The issue has been resolved by introducing a caching mechanism that ensures each field extension is applied only once, regardless of how many schemas the field appears in. Test cases have been added to validate this behavior and ensure that extensions are applied correctly.

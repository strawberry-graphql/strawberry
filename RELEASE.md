Release type: patch

This release fixes an issue where extensions were being duplicated when custom directives were added to the schema. Previously, when user directives were present, extensions were being appended twice to the extension list, causing them to be executed multiple times during query processing.

The fix ensures that extensions are added only once and maintains their original order. Test cases have been added to validate this behavior and ensure extensions are executed exactly once.

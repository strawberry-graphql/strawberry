Release type: patch

This release addresses a bug where directives were being added multiple times when defined in an interface which multiple objects inherits from.

The fix involves deduplicating directives when applying extensions/permissions to a field, ensuring that each directive is only added once.

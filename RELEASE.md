Release type: patch

This pull request addresses a bug where directives were being added multiple times, causing VSCode errors.
The fix involves deduplicating directives when applying extensions/permissions to a field, ensuring that each directive is only added once.

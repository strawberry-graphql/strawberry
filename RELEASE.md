Release type: patch

Refactor `ConnectionExtension` to copy arguments instead of extending them.
This should fix some issues with integrations which override `arguments`,
like the django one, where the inserted arguments were vanishing.

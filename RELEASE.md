Release type: patch

This release fixes the Flask view that was returning 400 when there were errors
in the GraphQL results. Now it always returns 200.

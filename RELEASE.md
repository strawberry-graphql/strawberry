Release type: patch

This release exposes `get_arguments` in the schema_converter module to allow
integrations, such as strawberry-django, to reuse that functionality if needed.

This is an internal change with no impact for end users.

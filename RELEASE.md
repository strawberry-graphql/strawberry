Release type: patch

Added option for the export_schema command to override the output federation version.
ussage example: strawberry export-schema --federation-version=2.5

This change ONLY effect "strawberry export-schema" command and is fully backword-compatible without any logic change.

Warning: Please use with caution!!

If the schema define directives that are not supported by the specified version (in the override parameter) the schema
will still generate the output useing the value from the override, and may break at runtime.

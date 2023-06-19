Release type: patch

This release fixes an issue on StrawberryField.copy_with method
not copying its extensions and overwritten `_arguments`.

Also make sure that all lists/tuples in those types are copied as
new lists/tuples to avoid unexpected behavior.

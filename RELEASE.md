Release type: patch

This release updates Strawberry internally to no longer pass keywords arguments
to `pathlib.PurePath`. Support for supplying keyword arguments to
`pathlib.PurePath` is deprecated and scheduled for removal in Python 3.14

Release type: patch

This release restricts the `backports.cached_property` dependency to only be
installed when Python < 3.8. Since version 3.8 `cached_property` is included
in the builtin `functools`. The code is updated to use the builtin version
when Python >= 3.8.

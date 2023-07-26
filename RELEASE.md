Release type: patch

This release fixes an issue where annotations resolution for auto and lazy fields
using `Annotated` where not preserving the remaining arguments because of a
typo in the arguments filtering.

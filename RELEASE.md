Release type: minor

This release fixes an issue when creating concrete types from generic when
passing list objects.

It also changes how type names are generated from generic types, now
`Value[Optional[List[str]]]` generates `ValueOptionalListStr` instead of
`StrListOptionalValue` which was unnatural to read.

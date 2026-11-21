---
release type: patch
---

This release fixes the error raised when a field, argument or input field is
annotated with a bare `list` or `typing.List`, with no item type. Strawberry now
raises a `MissingListItemTypeError` telling you to specify the item type, for
example `list[int]`, instead of an unhelpful `ValueError`.

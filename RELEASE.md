Release type: patch

This release fixes a codegen bug.  Prior to this fix,
inline fragments would only include the last field defined
within its scope and all fields common with its siblings.

After this fix, all fields will be included in the
generated types.

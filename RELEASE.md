Release type: patch

Fix cross-module type resolving for fields and resolvers

The following two issues are now fixed:

- A field with a generic (typeless) resolver looks up the
  type relative to the resolver and not the class the field is
  defined in. (#1448)

- When inheriting fields from another class the origin of the
  fields are set to the inheriting class and not the class the
  field is defined in.

Both these issues could lead to a rather undescriptive error message:

> TypeError: (...) fields cannot be resolved. Unexpected type 'None'

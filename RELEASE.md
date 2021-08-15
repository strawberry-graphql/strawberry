Release type: patch

This releases fixes an issue where you were not allowed
to use duck typing and return a different type that the
type declared on the field when the type was implementing
an interface. Now this works as long as you return a type
that has the same shape as the field type.

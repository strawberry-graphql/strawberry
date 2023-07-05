Release type: patch

This fixes a regression from 0.190.0 where changes to the
return type of a field done by Field Extensions would not
be taken in consideration by the schema.

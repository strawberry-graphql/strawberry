Release type patch:

This releases improves the MyPy plugin to be more forgiving of
settings like `follow_imports = skip` which would break the
type checking.

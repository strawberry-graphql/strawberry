Release type: patch

This release fixes the following deprecation warning:

```
Failing to pass a value to the 'type_params' parameter of 'typing._eval_type' is deprecated,
as it leads to incorrect behaviour when calling typing._eval_type on a stringified annotation
that references a PEP 695 type parameter. It will be disallowed in Python 3.15.
```

This was only trigger in Python 3.13 and above.

# Module tests

This directory contains the modules needed for the
`test_cross_module_resolvers.py` file in the directory above.

## Problem

In an earlier strawberry version the resolver did add itself as the
origin of fields. This caused the type resolving to fail when using
a resolver from a different module:

```python
from other_module import generic_resolver


@strawberry.field
class Foo:
    bar: "Bar" = strawberry.field(resolver=generic_resolver)


@strawberry.field
class Bar:
    awesome: bool
```

Since the `origin` of the `Foo.bar` field was set to
`generic_resolver` the `Bar` type was not looked up relative to the
`Foo` class but the `generic_resolver` causing the type lookup to
fail.

## Robust tests

**Important**: For these tests not to mask any incorrect resolution
behavior, all type names are unique across all modules. E.g. when
importing `a.AObject` into the `c` module it is renamed to `C_AObject`.
This ensures that we can discern which module the object is coming from
and any incorrect resolution behavior can be detected.

## Submodules

This module contains four submodules which are used to test various
cross-module references:

- `a` contains standalone types
- `b` contains standalone types
- `c` contains types that either inherit from the types in the
    `a` and `b` module or contain references to them
- `x` contains typeless (generic) resolvers

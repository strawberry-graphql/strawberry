Release type: patch

This release fixes a regression when comparing a `StrawberryAnnotation`
instance with anything that is not also a `StrawberryAnnotation` instance,
which caused it to raise a `NotImplementedError`.

This reverts its behavior back to how it worked before, where it returns
`NotImplemented` instead, meaning that the comparison can be delegated to
the type being compared against or return `False` in case it doesn't define
an `__eq__` method.

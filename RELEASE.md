Release type: patch

This release fixes another issue with mypy where it wasn't able to identify strawberry fields.
It also now knows that fields with resolvers aren't put in the __init__ method of the class.

Release type: patch

This release changes how we check for conflicting resolver arguments to
exclude `self` from those checks, which were introduced on version 0.208.0.

It is a common pattern among integrations, such as the Django one, to
use `root: Model` in the resolvers for better typing inference.

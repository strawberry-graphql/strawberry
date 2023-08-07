Release type: minor

This release updates Strawberry's codebase to use new features in Python 3.8.
It also removes `backports.cached-property` from our dependencies, as we can
now rely on the standard library's `functools.cached_property`.

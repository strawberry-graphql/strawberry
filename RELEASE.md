Release type: patch

Fix lazy type resolution with relative imports

This fixes an issue where lazy types using relative imports (e.g., `strawberry.lazy(".module")`) would fail to resolve correctly when comparing with the `__main__` module, potentially causing "Type X is defined multiple times in the schema" errors during test isolation.

This ensures that the fully resolved module name is used when comparing with `__main__.__spec__.name`, rather than the relative import path.

from __future__ import annotations


class MissingOptionalDependenciesError(Exception):
    """Some optional dependencies that are required for a particular task are missing."""

    def __init__(
        self,
        *,
        packages: list[str] | None = None,
        extras: list[str] | None = None,
    ) -> None:
        """Initialize the error.

        Args:
            packages: List of packages that are required but missing.
            extras: List of extras that are required but missing.
        """
        packages = packages or []

        if extras:
            packages.append(f"'strawberry-graphql[{','.join(extras)}]'")

        hint = f" (hint: pip install {' '.join(packages)})" if packages else ""

        self.message = f"Some optional dependencies are missing{hint}"

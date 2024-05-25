from __future__ import annotations

from typing import Optional


class MissingOptionalDependenciesError(Exception):
    """Some optional dependencies that are required for a particular
    task are missing."""

    def __init__(
        self,
        *,
        packages: Optional[list[str]] = None,
        extras: Optional[list[str]] = None,
    ) -> None:
        packages = packages or []
        if extras:
            packages.append(f"'strawberry-graphql[{','.join(extras)}]'")
        hint = f" (hint: pip install {' '.join(packages)})" if packages else ""
        self.message = f"Some optional dependencies are missing{hint}"

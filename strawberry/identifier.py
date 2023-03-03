from dataclasses import dataclass
from typing import Callable, Optional


def default_version_comparator(version1: str, version2: str) -> int:
    if version1 == version2:
        return 0
    if version1 > version2:
        return 1
    return -1


@dataclass
class SchemaIdentifier:
    name: str
    version: str
    version_comparator: Callable[[str], int] = default_version_comparator


@dataclass
class SupportedSchema:
    name: Optional[str] = None
    from_version: Optional[str] = None
    until_version: Optional[str] = None

    def matches(self, schema_identifier: Optional[SchemaIdentifier]) -> bool:
        if not schema_identifier:
            return False
        if schema_identifier.name != self.name:
            return False
        if (
            self.from_version
            and schema_identifier.version_comparator(
                schema_identifier.version, self.from_version
            )
            < 0
        ):
            return False
        if (
            self.until_version
            and schema_identifier.version_comparator(
                schema_identifier.version, self.until_version
            )
            > 0
        ):
            return False
        return True

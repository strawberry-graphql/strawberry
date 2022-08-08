import dataclasses
from typing import Set


@dataclasses.dataclass
class PrintExtras:
    directives: Set[str] = dataclasses.field(default_factory=set)
    types: Set[type] = dataclasses.field(default_factory=set)

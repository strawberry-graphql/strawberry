from dataclasses import dataclass, field
from typing import Dict


@dataclass
class TemporalResponse:
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)


__all__ = ["TemporalResponse"]

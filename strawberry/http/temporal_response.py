from dataclasses import dataclass


@dataclass
class TemporalResponse:
    status_code: int = 200

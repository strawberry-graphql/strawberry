from dataclasses import dataclass, field


@dataclass
class TemporalResponse:
    status_code: int = 200
    headers: dict[str, str] = field(default_factory=dict)


__all__ = ["TemporalResponse"]

from __future__ import annotations

import dataclasses
import re
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path


_SCALAR_TARGET_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*$")


@dataclasses.dataclass(frozen=True)
class CodegenConfig:
    scalars: dict[str, str] = dataclasses.field(default_factory=dict)


def load_config(path: Path) -> CodegenConfig:
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in config file {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise TypeError(
            f"Config file {path} must contain a YAML mapping at the top level, "
            f"got {type(raw).__name__}."
        )

    scalars_raw = raw.get("scalars", {})

    if not isinstance(scalars_raw, dict):
        raise TypeError(
            f"`scalars` in {path} must be a mapping of scalar name to "
            f'"<module>:<object>", got {type(scalars_raw).__name__}.'
        )

    scalars: dict[str, str] = {}

    for name, target in scalars_raw.items():
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(
                f"Invalid scalar name {name!r} in {path}: must be a valid "
                f"Python identifier."
            )
        if not isinstance(target, str) or not _SCALAR_TARGET_RE.match(target):
            raise ValueError(
                f"Invalid target {target!r} for scalar {name!r} in {path}: "
                f'expected "<module>:<object>" (e.g. "strawberry.scalars:JSON").'
            )
        scalars[name] = target

    return CodegenConfig(scalars=scalars)

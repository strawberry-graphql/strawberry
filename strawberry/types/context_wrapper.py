from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ContextWrapper:
    context: Optional[Any]
    extensions: Optional[Dict[str, Any]]

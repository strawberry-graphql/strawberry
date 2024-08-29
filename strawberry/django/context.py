from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


@dataclass
class StrawberryDjangoContext:
    request: HttpRequest
    response: HttpResponse

    def __getitem__(self, key: str) -> Any:
        # __getitem__ override needed to avoid issues for who's
        # using info.context["request"]
        return super().__getattribute__(key)

    def get(self, key: str) -> Any:
        """Enable .get notation for accessing the request."""
        return super().__getattribute__(key)


__all__ = ["StrawberryDjangoContext"]

"""Origin validation for WebSocket handshakes.

Browsers don't apply CORS to WebSocket handshakes: a page on any origin can open
a socket to a GraphQL endpoint, and the browser attaches the user's cookies to
the request. Checking the ``Origin`` header before accepting the connection is
the standard defence against this (cross-site WebSocket hijacking).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from collections.abc import Iterable

_DEFAULT_PORTS = {"http": ":80", "https": ":443"}


def normalize_origin(origin: str) -> str:
    """Return ``origin`` in the form browsers send it in the ``Origin`` header.

    Browsers send the scheme and host in lowercase and leave out default ports,
    so ``"https://Example.com:443"`` becomes ``"https://example.com"``.
    """
    parts = urlsplit(origin.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    default_port = _DEFAULT_PORTS.get(scheme)
    if default_port and netloc.endswith(default_port):
        netloc = netloc.removesuffix(default_port)

    return f"{scheme}://{netloc}"


def normalize_allowed_origins(allowed_origins: Iterable[str]) -> frozenset[str]:
    """Validate and normalize the origins passed as ``allowed_origins``."""
    if isinstance(allowed_origins, str):
        raise TypeError(
            "allowed_origins must be a sequence of origins, not a string. "
            f"Did you mean [{allowed_origins!r}]?"
        )

    normalized: set[str] = set()

    for origin in allowed_origins:
        if origin == "*":
            normalized.add(origin)
            continue

        parts = urlsplit(origin)
        if (
            not parts.scheme
            or not parts.netloc
            or parts.path not in ("", "/")
            or parts.query
            or parts.fragment
        ):
            raise ValueError(
                f"Invalid origin {origin!r} in allowed_origins. Expected '*' or "
                "an origin like 'https://example.com' (scheme, host and optional "
                "port, without a path)."
            )

        normalized.add(normalize_origin(origin))

    return frozenset(normalized)


def is_same_origin(origin: str, host: str | None) -> bool:
    """Check whether ``origin`` points at the host the request was sent to.

    Like gorilla/websocket and Tornado, this compares the host and port only, so
    TLS terminated at a proxy (an ``https`` page reaching the app over ``http``)
    still counts as the same origin.
    """
    if not host:
        return False

    netloc = urlsplit(origin).netloc
    return bool(netloc) and netloc.lower() == host.strip().lower()


__all__ = ["is_same_origin", "normalize_allowed_origins", "normalize_origin"]

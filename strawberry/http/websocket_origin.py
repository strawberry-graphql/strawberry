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

_DEFAULT_PORTS = {"http": 80, "https": 443}


def _format_host(hostname: str) -> str:
    # `urlsplit` strips the brackets around IPv6 addresses
    return f"[{hostname}]" if ":" in hostname else hostname


def normalize_origin(origin: str) -> str | None:
    """Return ``origin`` in the form browsers send it in the ``Origin`` header.

    Browsers send the scheme and host in lowercase and leave out default ports,
    so ``"https://Example.com:443"`` becomes ``"https://example.com"``. Returns
    ``None`` for values that aren't origins, such as ``"null"`` or ``"https://["``.
    """
    try:
        parts = urlsplit(origin.strip())
        port = parts.port
    except ValueError:
        return None

    if not parts.scheme or not parts.hostname:
        return None

    scheme = parts.scheme.lower()
    host = _format_host(parts.hostname)

    if port is not None and port != _DEFAULT_PORTS.get(scheme):
        host = f"{host}:{port}"

    return f"{scheme}://{host}"


def _has_more_than_an_origin(url: str) -> bool:
    parts = urlsplit(url.strip())
    return bool(
        parts.path not in ("", "/") or parts.query or parts.fragment or parts.username
    )


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

        normalized_origin = normalize_origin(origin)

        if normalized_origin is None or _has_more_than_an_origin(origin):
            raise ValueError(
                f"Invalid origin {origin!r} in allowed_origins. Expected '*' or "
                "an origin like 'https://example.com' (scheme, host and optional "
                "port, without a path)."
            )

        normalized.add(normalized_origin)

    return frozenset(normalized)


def is_same_origin(origin: str, host: str | None) -> bool:
    """Check whether ``origin`` points at the host the request was sent to.

    Like gorilla/websocket and Tornado, this compares the host and port only, so
    TLS terminated at a proxy (an ``https`` page reaching the app over ``http``)
    still counts as the same origin. Ports left out on either side are the
    default port for the origin's scheme, so ``Host: example.com:443`` matches
    ``Origin: https://example.com``.
    """
    if not host:
        return False

    try:
        origin_parts = urlsplit(origin)
        host_parts = urlsplit(f"//{host.strip()}")
        default_port = _DEFAULT_PORTS.get(origin_parts.scheme.lower())
        origin_port = origin_parts.port or default_port
        host_port = host_parts.port or default_port
    except ValueError:
        return False

    return (
        origin_parts.hostname is not None
        and origin_parts.hostname == host_parts.hostname
        and origin_port == host_port
    )


__all__ = ["is_same_origin", "normalize_allowed_origins", "normalize_origin"]

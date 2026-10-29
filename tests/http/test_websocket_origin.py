import pytest

from strawberry.http.websocket_origin import (
    is_same_origin,
    normalize_allowed_origins,
    normalize_origin,
)


@pytest.mark.parametrize(
    ("origin", "expected"),
    [
        ("https://example.com", "https://example.com"),
        ("HTTPS://Example.COM", "https://example.com"),
        ("https://example.com:443", "https://example.com"),
        ("http://example.com:80", "http://example.com"),
        ("https://example.com:8443", "https://example.com:8443"),
        ("http://example.com:443", "http://example.com:443"),
        ("http://localhost:5173", "http://localhost:5173"),
        ("http://[::1]:8000", "http://[::1]:8000"),
    ],
)
def test_normalize_origin(origin: str, expected: str):
    assert normalize_origin(origin) == expected


def test_normalize_allowed_origins():
    assert normalize_allowed_origins(
        ["https://App.example.com:443", "https://app.example.com/", "*"]
    ) == frozenset({"https://app.example.com", "*"})


@pytest.mark.parametrize(
    "origin",
    [
        "app.example.com",
        "https://",
        "https://example.com/graphql",
        "https://example.com?x=1",
        "https://example.com#x",
        "*.example.com",
    ],
)
def test_normalize_allowed_origins_rejects_invalid_origins(origin: str):
    with pytest.raises(ValueError, match="Invalid origin"):
        normalize_allowed_origins([origin])


def test_normalize_allowed_origins_rejects_a_bare_string():
    with pytest.raises(TypeError, match=r"Did you mean \['https://example.com'\]"):
        normalize_allowed_origins("https://example.com")


@pytest.mark.parametrize(
    ("origin", "host", "expected"),
    [
        ("https://example.com", "example.com", True),
        ("https://Example.com", "example.COM", True),
        # Schemes aren't compared, so TLS terminated at a proxy still matches
        ("http://example.com", "example.com", True),
        ("http://localhost:8000", "localhost:8000", True),
        ("http://localhost:5173", "localhost:8000", False),
        ("https://other.example.com", "example.com", False),
        ("https://example.com.evil.com", "example.com", False),
        ("null", "example.com", False),
        ("https://example.com", None, False),
        ("https://example.com", "", False),
    ],
)
def test_is_same_origin(origin: str, host: str | None, expected: bool):
    assert is_same_origin(origin, host) is expected

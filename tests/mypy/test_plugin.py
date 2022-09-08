from decimal import Decimal

import pytest

from strawberry.ext.mypy_plugin import FALLBACK_VERSION, MypyVersion, plugin


@pytest.fixture
def maintain_version():
    """Clean-up side-effected version after tests"""

    yield

    del MypyVersion.VERSION


@pytest.mark.parametrize(
    "version, expected",
    [
        ("0.93", Decimal("0.93")),
        ("0.800", Decimal("0.800")),
        ("0.920", Decimal("0.920")),
        ("01.100", FALLBACK_VERSION),  # Invalid version should revert to fallback
        ("0.980+dev.d89b28d973c3036ef154c9551b961d9119761380", Decimal("0.980")),
    ],
)
@pytest.mark.usefixtures("maintain_version")
def test_plugin(version, expected):

    plugin(version)
    assert MypyVersion.VERSION == expected

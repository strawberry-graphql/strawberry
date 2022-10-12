from decimal import Decimal

import pytest

from strawberry.ext.mypy_plugin import FALLBACK_VERSION, MypyVersion, plugin


pytestmark = pytest.mark.usefixtures("maintain_version")


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
        ("0.980+dev.d89b28d973c3036ef154c9551b961d9119761380", Decimal("0.980")),
        ("1.0.0", Decimal("1.0")),
        ("99.999", Decimal("99.999")),
    ],
)
def test_plugin(version, expected):

    plugin(version)
    assert MypyVersion.VERSION == expected


def test_plugin_negative():
    invalid_version = "001.290"
    with pytest.warns(UserWarning, match=f"Mypy version {invalid_version} could not"):
        plugin(invalid_version)
        assert MypyVersion.VERSION == FALLBACK_VERSION

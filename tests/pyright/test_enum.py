from .utils import Result, requires_pyright, run_pyright, skip_on_windows

pytestmark = [skip_on_windows, requires_pyright]


CODE_WITH_DECORATOR = """
from enum import Enum

import strawberry

@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"

reveal_type(IceCreamFlavour)
reveal_type(IceCreamFlavour.VANILLA)
"""


def test_enum_with_decorator():
    results = run_pyright(CODE_WITH_DECORATOR)

    assert results == [
        Result(
            type="information",
            message='Type of "IceCreamFlavour" is "type[IceCreamFlavour]"',
            line=12,
            column=13,
        ),
        Result(
            type="information",
            message=(
                'Type of "IceCreamFlavour.VANILLA" is '
                '"Literal[IceCreamFlavour.VANILLA]"'
            ),
            line=13,
            column=13,
        ),
    ]


CODE_WITH_DECORATOR_AND_NAME = """
from enum import Enum

import strawberry

@strawberry.enum(name="IceCreamFlavour")
class Flavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"

reveal_type(Flavour)
reveal_type(Flavour.VANILLA)
"""


def test_enum_with_decorator_and_name():
    results = run_pyright(CODE_WITH_DECORATOR_AND_NAME)

    assert results == [
        Result(
            type="information",
            message='Type of "Flavour" is "type[Flavour]"',
            line=12,
            column=13,
        ),
        Result(
            type="information",
            message='Type of "Flavour.VANILLA" is "Literal[Flavour.VANILLA]"',
            line=13,
            column=13,
        ),
    ]


CODE_WITH_MANUAL_DECORATOR = """
from enum import Enum

import strawberry

class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"

reveal_type(strawberry.enum(IceCreamFlavour))
reveal_type(strawberry.enum(IceCreamFlavour).VANILLA)
"""


def test_enum_with_manual_decorator():
    results = run_pyright(CODE_WITH_MANUAL_DECORATOR)

    assert results == [
        Result(
            type="information",
            message=(
                'Type of "strawberry.enum(IceCreamFlavour)" '
                'is "type[IceCreamFlavour]"'
            ),
            line=11,
            column=13,
        ),
        Result(
            type="information",
            message=(
                'Type of "strawberry.enum(IceCreamFlavour).VANILLA" '
                'is "Literal[IceCreamFlavour.VANILLA]"'
            ),
            line=12,
            column=13,
        ),
    ]


CODE_WITH_MANUAL_DECORATOR_AND_NAME = """
from enum import Enum

import strawberry

class Flavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"

reveal_type(strawberry.enum(name="IceCreamFlavour")(Flavour))
reveal_type(strawberry.enum(name="IceCreamFlavour")(Flavour).VANILLA)
"""


def test_enum_with_manual_decorator_and_name():
    results = run_pyright(CODE_WITH_MANUAL_DECORATOR_AND_NAME)

    assert results == [
        Result(
            type="information",
            message=(
                'Type of "strawberry.enum(name="IceCreamFlavour")(Flavour)" '
                'is "type[Flavour]"'
            ),
            line=11,
            column=13,
        ),
        Result(
            type="information",
            message=(
                'Type of "strawberry.enum(name="IceCreamFlavour")(Flavour).VANILLA" '
                'is "Literal[Flavour.VANILLA]"'
            ),
            line=12,
            column=13,
        ),
    ]


CODE_WITH_DEPRECATION_REASON = """
from enum import Enum

import strawberry

@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = strawberry.enum_value(
        "strawberry", deprecation_reason="We ran out"
    )
    CHOCOLATE = "chocolate"

reveal_type(IceCreamFlavour)
reveal_type(IceCreamFlavour.STRAWBERRY)
"""


def test_enum_deprecated():
    results = run_pyright(CODE_WITH_DEPRECATION_REASON)

    assert results == [
        Result(
            type="information",
            message='Type of "IceCreamFlavour" is "type[IceCreamFlavour]"',
            line=14,
            column=13,
        ),
        Result(
            type="information",
            message=(
                'Type of "IceCreamFlavour.STRAWBERRY" is '
                '"Literal[IceCreamFlavour.STRAWBERRY]"'
            ),
            line=15,
            column=13,
        ),
    ]

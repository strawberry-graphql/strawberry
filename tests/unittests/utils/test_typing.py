from typing import Optional, Union

from strawberry.utils.typing import get_optional_annotation


def test_get_optional_annotation():

    # Pair Union
    assert get_optional_annotation(Optional[Union[str, bool]]) == Union[str, bool]

    # More than pair Union
    assert (
        get_optional_annotation(Optional[Union[str, int, bool]])
        == Union[str, int, bool]
    )

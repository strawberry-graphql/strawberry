from inline_snapshot import snapshot

from .utils.marks import requires_mypy, requires_pyright, requires_ty, skip_on_windows
from .utils.typecheck import typecheck

pytestmark = [skip_on_windows, requires_pyright, requires_mypy, requires_ty]


# Strawberry types are not ordered dataclasses, so defining a custom comparison
# operator must not be reported as conflicting with a generated one.
CODE = """
import strawberry


@strawberry.type
class Fruit:
    weight: int

    def __gt__(self, other: "Fruit") -> bool:
        return self.weight > other.weight
"""


def test():
    results = typecheck(CODE)

    assert results.pyright == snapshot([])
    assert results.mypy == snapshot([])
    assert results.ty == snapshot([])

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.lazy_type import LazyType


@strawberry.type
class LaziestType:
    something: bool


def test_lazy_type():
    # This type is in the same file but should adequately test the logic.
    # Module path is short and relative because of the way pytest runs the file
    LazierType = LazyType["LaziestType", "test_lazy_types"]

    annotation = StrawberryAnnotation(LazierType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved is LazierType
    assert resolved.resolve_type() is LaziestType

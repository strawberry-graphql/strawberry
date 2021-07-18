import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.lazy_type import LazyType


@strawberry.type
class LazierType:
    something: bool


def test_lazy_type():
    # This type is in the same file but should adequately test the logic
    LaziestType = LazyType["LazierType", "tests.types.resolving.test_lazy_type"]

    annotation = StrawberryAnnotation(LaziestType)
    resolved = annotation.resolve()

    # Currently StrawberryAnnotation(LazyType).resolve() returns the unresolved
    # LazyType. We may want to find a way to directly return the referenced object
    # without a second resolving step.
    assert isinstance(resolved, LazyType)
    assert resolved.resolve_type() is LazierType

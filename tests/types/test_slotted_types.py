import sys

import strawberry


slots = True


def test_simple_type():
    @strawberry.type(slots=False)
    class SimpleTypeNoSlot:
        a: int = strawberry.field()

    @strawberry.type(slots=slots)
    class SimpleType:
        a: int = strawberry.field()

    slotted = SimpleType(1)
    assert slotted.a == 1
    unslotted = SimpleTypeNoSlot(1)
    assert sys.getsizeof(slotted) < sys.getsizeof(unslotted)


def test_single_inheritance_tree():
    @strawberry.type(slots=slots)
    class A:  # shared parent, ok
        a: int = strawberry.field()
        b: int = strawberry.field()

    @strawberry.type(slots=slots)
    class B(A):
        c: int = strawberry.field()

    @strawberry.type(slots=slots)
    class C(B):
        d: int = strawberry.field()
        e: int = strawberry.field()

    A(100, 100)
    B(100, 100, 100)
    C(100, 100, 100, 100, 100)


def test_multiple_inheritance():
    @strawberry.type(slots=slots)
    class A:  # shared parent, ok
        a: int = strawberry.field()
        b: int = strawberry.field()

    @strawberry.type(slots=slots)
    class B:
        c: int = strawberry.field()

    @strawberry.type(slots=slots)
    class C(A, B):
        d: int = strawberry.field()
        e: int = strawberry.field()

    A(100, 100)
    B(100, 100, 100)
    C(100, 100, 100, 100, 100)


def test_field_overriden_warns():
    raise NotImplementedError("TODO")

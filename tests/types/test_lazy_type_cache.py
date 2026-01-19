"""Regression tests for lazy type resolution to prevent duplicate type errors.

The fix relies on importlib.import_module() using sys.modules, which caches
imported modules and ensures the same module object is returned on subsequent
imports (unless explicitly reloaded).
"""

import importlib
import sys
import types
from typing import Annotated

import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.types.base import get_object_definition
from strawberry.types.lazy_type import LazyType


@strawberry.type
class User:
    name: str


@strawberry.input
class UserFilter:
    name: str


def test_lazy_type_uses_sys_modules():
    """Test that LazyType uses sys.modules for consistency."""
    module_name = "tests.types.test_lazy_type_cache"

    # Ensure module is in sys.modules
    if module_name not in sys.modules:
        importlib.import_module(module_name)

    lazy_type = LazyType("User", module_name)
    resolved = lazy_type.resolve_type()

    # Should get the User class from sys.modules
    assert resolved is User
    module_from_sys = sys.modules[module_name]
    assert resolved is module_from_sys.User


def test_lazy_type_consistent_across_multiple_resolutions():
    """Test that multiple resolutions return the same type."""
    module_name = "tests.types.test_lazy_type_cache"

    lazy_type = LazyType("User", module_name)

    resolved1 = lazy_type.resolve_type()
    resolved2 = lazy_type.resolve_type()
    resolved3 = lazy_type.resolve_type()

    assert resolved1 is User
    assert resolved2 is User
    assert resolved3 is User
    assert resolved1 is resolved2 is resolved3


def test_lazy_type_with_package():
    """Test that LazyType works with relative imports."""
    lazy_type = LazyType("UserFilter", ".test_lazy_type_cache", "tests.types")

    resolved = lazy_type.resolve_type()
    assert resolved is UserFilter


def test_lazy_type_with_relative_import_resolves_main_module():
    """Test that __main__ resolution works with relative imports."""
    fake_main = types.ModuleType("__main__")
    fake_main.__file__ = None
    fake_main.__spec__ = types.SimpleNamespace(name="tests.types.test_lazy_type_cache")

    @strawberry.input
    class MainUserFilter:
        email: str

    fake_main.MainUserFilter = MainUserFilter

    original_main = sys.modules.get("__main__")

    try:
        sys.modules["__main__"] = fake_main

        lazy_type = LazyType("MainUserFilter", ".test_lazy_type_cache", "tests.types")
        resolved = lazy_type.resolve_type()

        assert resolved is MainUserFilter
        assert resolved is fake_main.MainUserFilter

    finally:
        if original_main is not None:
            sys.modules["__main__"] = original_main
        else:
            sys.modules.pop("__main__", None)


def test_lazy_type_with_annotated():
    """Test lazy types work with Annotated syntax."""
    LazyUser = Annotated["User", strawberry.lazy("tests.types.test_lazy_type_cache")]

    @strawberry.type
    class Post:
        title: str
        author: LazyUser

    definition = get_object_definition(Post)
    author_field = definition.fields[1]

    annotation = StrawberryAnnotation(author_field.type)
    resolved = annotation.resolve()

    assert isinstance(resolved, LazyType)
    resolved_type = resolved.resolve_type()
    assert resolved_type is User

    resolved_type2 = resolved.resolve_type()
    assert resolved_type2 is User
    assert resolved_type2 is resolved_type


def test_schema_building_with_lazy_types_no_duplicates():
    """Test that building a schema with lazy types doesn't create duplicates."""
    LazyUserFilter = Annotated[
        "UserFilter", strawberry.lazy("tests.types.test_lazy_type_cache")
    ]

    @strawberry.type
    class Query:
        @strawberry.field
        def users(self, filters: LazyUserFilter | None = None) -> list[User]:
            return []

    schema = strawberry.Schema(query=Query)
    assert schema is not None

    introspection = schema.introspect()
    type_names = [t["name"] for t in introspection["__schema"]["types"]]
    assert "UserFilter" in type_names


def test_multiple_lazy_references_same_type():
    """Test that multiple lazy references to the same type resolve consistently."""
    LazyUser1 = Annotated["User", strawberry.lazy("tests.types.test_lazy_type_cache")]
    LazyUser2 = Annotated["User", strawberry.lazy("tests.types.test_lazy_type_cache")]

    @strawberry.type
    class Post:
        author: LazyUser1
        editor: LazyUser2

    @strawberry.type
    class Query:
        @strawberry.field
        def posts(self) -> list[Post]:
            return []

    schema = strawberry.Schema(query=Query)
    assert schema is not None

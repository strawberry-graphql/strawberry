from sys import modules
from types import ModuleType

import strawberry


deferred_module_source = """
from __future__ import annotations

import strawberry

@strawberry.type
class User:
    username: str
    email: str

@strawberry.interface
class UserContent:
    created_by: User
"""


def test_deferred_other_module():
    mod = ModuleType("tests.deferred_module")
    modules[mod.__name__] = mod

    try:
        exec(deferred_module_source, mod.__dict__)

        @strawberry.type
        class Post(mod.UserContent):
            title: str
            body: str

        definition = Post._type_definition
        assert definition.fields[0].type == mod.User
    finally:
        del modules[mod.__name__]

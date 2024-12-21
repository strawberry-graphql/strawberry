import base64
import dataclasses
import re
import sys
from enum import Enum
from typing import Any, NewType, Optional, TypeVar, Union

import pytest
from pydantic import BaseModel, Field, ValidationError

import strawberry
from strawberry.experimental.pydantic._compat import (
    IS_PYDANTIC_V2,
    CompatModelField,
    PydanticCompat,
)
from strawberry.experimental.pydantic.exceptions import (
    AutoFieldsNotInBaseModelError,
    BothDefaultAndDefaultFactoryDefinedError,
)
from strawberry.experimental.pydantic.utils import get_default_factory_for_field
from strawberry.types.base import (
    StrawberryList,
    StrawberryObjectDefinition,
    StrawberryOptional,
)
from tests.experimental.pydantic.utils import needs_pydantic_v1


def test_can_use_type_standalone():
    class User(BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: strawberry.auto

    user = UserType(age=1, password="abc")

    assert user.age == 1
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry():
    class User(BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: strawberry.auto

    origin_user = User(age=1, password="abc")
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.password == "abc"


def test_cannot_convert_pydantic_type_to_strawberry_missing_field():
    class User(BaseModel):
        age: int

    with pytest.raises(
        AutoFieldsNotInBaseModelError,
        match=re.escape(
            "UserType defines ['password'] with strawberry.auto."
            " Field(s) not present in User BaseModel."
        ),
    ):

        @strawberry.experimental.pydantic.type(User)
        class UserType:
            age: strawberry.auto
            password: strawberry.auto


def test_cannot_convert_pydantic_type_to_strawberry_property_auto():
    # auto inferring type of a property is not supported

    class User(BaseModel):
        age: int

        @property
        def password(self) -> str:
            return "hunter2"

    with pytest.raises(
        AutoFieldsNotInBaseModelError,
        match=re.escape(
            "UserType defines ['password'] with strawberry.auto."
            " Field(s) not present in User BaseModel."
        ),
    ):

        @strawberry.experimental.pydantic.type(User)
        class UserType:
            age: strawberry.auto
            password: strawberry.auto


def test_can_convert_pydantic_type_to_strawberry_property():
    class User(BaseModel):
        age: int

        @property
        def password(self) -> str:
            return "hunter2"

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: str

    origin_user = User(age=1)
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.password == "hunter2"


def test_can_convert_alias_pydantic_field_to_strawberry():
    class UserModel(BaseModel):
        age_: int = Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age_: strawberry.auto
        password: strawberry.auto

    origin_user = UserModel(age=1, password="abc")
    user = User.from_pydantic(origin_user)

    assert user.age_ == 1
    assert user.password == "abc"


def test_convert_alias_name():
    class UserModel(BaseModel):
        age_: int = Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=True
    )
    class User: ...

    origin_user = UserModel(age=1, password="abc")
    user = User.from_pydantic(origin_user)
    assert user.age_ == 1
    definition = User.__strawberry_definition__

    assert definition.fields[0].graphql_name == "age"


def test_do_not_convert_alias_name():
    class UserModel(BaseModel):
        age_: int = Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(
        UserModel, all_fields=True, use_pydantic_alias=False
    )
    class User: ...

    origin_user = UserModel(age=1, password="abc")
    user = User.from_pydantic(origin_user)
    assert user.age_ == 1
    definition = User.__strawberry_definition__

    assert definition.fields[0].graphql_name is None


def test_can_pass_pydantic_field_description_to_strawberry():
    class UserModel(BaseModel):
        age: int
        password: Optional[str] = Field(..., description="NOT 'password'.")

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

    definition = User.__strawberry_definition__

    assert definition.fields[0].python_name == "age"
    assert definition.fields[0].description is None

    assert definition.fields[1].python_name == "password"
    assert definition.fields[1].description == "NOT 'password'."


def test_can_convert_falsy_values_to_strawberry():
    class UserModel(BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

    origin_user = UserModel(age=0, password="")
    user = User.from_pydantic(origin_user)

    assert user.age == 0
    assert not user.password


def test_can_convert_pydantic_type_to_strawberry_with_private_field():
    class UserModel(BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(model=UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.Private[str]

    user = User(age=30, password="qwerty")
    assert user.age == 30
    assert user.password == "qwerty"

    definition = User.__strawberry_definition__
    assert len(definition.fields) == 1
    assert definition.fields[0].python_name == "age"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type is int


def test_can_convert_pydantic_type_with_nested_data_to_strawberry():
    class WorkModel(BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    class UserModel(BaseModel):
        work: WorkModel

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(work=WorkModel(name="Ice Cream inc"))
    user = User.from_pydantic(origin_user)

    assert user.work.name == "Ice Cream inc"


def test_can_convert_pydantic_type_with_list_of_nested_data_to_strawberry():
    class WorkModel(BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    class UserModel(BaseModel):
        work: list[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(
        work=[
            WorkModel(name="Ice Cream inc"),
            WorkModel(name="Wall Street"),
        ]
    )
    user = User.from_pydantic(origin_user)

    assert user.work == [Work(name="Ice Cream inc"), Work(name="Wall Street")]


def test_can_convert_pydantic_type_with_list_of_nested_int_to_strawberry():
    class UserModel(BaseModel):
        hours: list[int]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        hours: strawberry.auto

    origin_user = UserModel(
        hours=[
            8,
            9,
            10,
        ]
    )
    user = User.from_pydantic(origin_user)

    assert user.hours == [8, 9, 10]


def test_can_convert_pydantic_type_with_matrix_list_of_nested_int_to_strawberry():
    class UserModel(BaseModel):
        hours: list[list[int]]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        hours: strawberry.auto

    origin_user = UserModel(
        hours=[
            [8, 10],
            [9, 11],
            [10, 12],
        ]
    )
    user = User.from_pydantic(origin_user)

    assert user.hours == [
        [8, 10],
        [9, 11],
        [10, 12],
    ]


def test_can_convert_pydantic_type_with_matrix_list_of_nested_model_to_strawberry():
    class HourModel(BaseModel):
        hour: int

    @strawberry.experimental.pydantic.type(HourModel)
    class Hour:
        hour: strawberry.auto

    class UserModel(BaseModel):
        hours: list[list[HourModel]]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        hours: strawberry.auto

    origin_user = UserModel(
        hours=[
            [
                HourModel(hour=1),
                HourModel(hour=2),
            ],
            [
                HourModel(hour=3),
                HourModel(hour=4),
            ],
            [
                HourModel(hour=5),
                HourModel(hour=6),
            ],
        ]
    )
    user = User.from_pydantic(origin_user)

    assert user.hours == [
        [
            Hour(hour=1),
            Hour(hour=2),
        ],
        [
            Hour(hour=3),
            Hour(hour=4),
        ],
        [
            Hour(hour=5),
            Hour(hour=6),
        ],
    ]


def test_can_convert_pydantic_type_to_strawberry_with_union():
    class BranchA(BaseModel):
        field_a: str

    class BranchB(BaseModel):
        field_b: int

    class User(BaseModel):
        age: int
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.type(BranchA)
    class BranchAType:
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchB)
    class BranchBType:
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        union_field: strawberry.auto

    origin_user = User(age=1, union_field=BranchA(field_a="abc"))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchAType)
    assert user.union_field.field_a == "abc"

    origin_user = User(age=1, union_field=BranchB(field_b=123))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchBType)
    assert user.union_field.field_b == 123


def test_can_convert_pydantic_type_to_strawberry_with_union_of_strawberry_types():
    @strawberry.type
    class BranchA:
        field_a: str

    @strawberry.type
    class BranchB:
        field_b: int

    class User(BaseModel):
        age: int
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        union_field: strawberry.auto

    origin_user = User(age=1, union_field=BranchA(field_a="abc"))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchA)
    assert user.union_field.field_a == "abc"

    origin_user = User(age=1, union_field=BranchB(field_b=123))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchB)
    assert user.union_field.field_b == 123


def test_can_convert_pydantic_type_to_strawberry_with_union_nullable():
    class BranchA(BaseModel):
        field_a: str

    class BranchB(BaseModel):
        field_b: int

    class User(BaseModel):
        age: int
        union_field: Union[None, BranchA, BranchB]

    @strawberry.experimental.pydantic.type(BranchA)
    class BranchAType:
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchB)
    class BranchBType:
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        union_field: strawberry.auto

    origin_user = User(age=1, union_field=BranchA(field_a="abc"))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchAType)
    assert user.union_field.field_a == "abc"

    origin_user = User(age=1, union_field=BranchB(field_b=123))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.union_field, BranchBType)
    assert user.union_field.field_b == 123

    origin_user = User(age=1, union_field=None)
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.union_field is None


def test_can_convert_pydantic_type_to_strawberry_with_enum():
    @strawberry.enum
    class UserKind(Enum):
        user = 0
        admin = 1

    class User(BaseModel):
        age: int
        kind: UserKind

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        kind: strawberry.auto

    origin_user = User(age=1, kind=UserKind.user)
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.kind == UserKind.user


def test_can_convert_pydantic_type_to_strawberry_with_interface():
    class Base(BaseModel):
        base_field: str

    class BranchA(Base):
        field_a: str

    class BranchB(Base):
        field_b: int

    class User(BaseModel):
        age: int
        interface_field: Base

    @strawberry.experimental.pydantic.interface(Base)
    class BaseType:
        base_field: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchA)
    class BranchAType(BaseType):
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.type(BranchB)
    class BranchBType(BaseType):
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        interface_field: strawberry.auto

    origin_user = User(age=1, interface_field=BranchA(field_a="abc", base_field="def"))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.interface_field, BranchAType)
    assert user.interface_field.field_a == "abc"

    origin_user = User(age=1, interface_field=BranchB(field_b=123, base_field="def"))
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert isinstance(user.interface_field, BranchBType)
    assert user.interface_field.field_b == 123


def test_can_convert_pydantic_type_to_strawberry_with_additional_fields():
    class UserModel(BaseModel):
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: int
        password: strawberry.auto

    origin_user = UserModel(password="abc")
    user = User.from_pydantic(origin_user, extra={"age": 1})

    assert user.age == 1
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry_with_additional_nested_fields():
    @strawberry.type
    class Work:
        name: str

    class UserModel(BaseModel):
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: Work
        password: strawberry.auto

    origin_user = UserModel(password="abc")
    user = User.from_pydantic(origin_user, extra={"work": {"name": "Ice inc"}})

    assert user.work.name == "Ice inc"
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry_with_additional_list_nested_fields():
    @strawberry.type
    class Work:
        name: str

    class UserModel(BaseModel):
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: list[Work]
        password: strawberry.auto

    origin_user = UserModel(password="abc")
    user = User.from_pydantic(
        origin_user,
        extra={
            "work": [
                {"name": "Software inc"},
                {"name": "Homemade inc"},
            ]
        },
    )

    assert user.work == [
        Work(name="Software inc"),
        Work(name="Homemade inc"),
    ]
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry_with_missing_data_in_nested_type():
    class WorkModel(BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        year: int
        name: strawberry.auto

    class UserModel(BaseModel):
        work: list[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(work=[WorkModel(name="Software inc")])

    user = User.from_pydantic(
        origin_user,
        extra={
            "work": [
                {"year": 2020},
            ]
        },
    )

    assert user.work == [
        Work(name="Software inc", year=2020),
    ]


def test_can_convert_pydantic_type_to_strawberry_with_missing_index_data_nested_type():
    class WorkModel(BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        year: int
        name: strawberry.auto

    class UserModel(BaseModel):
        work: list[Optional[WorkModel]]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(
        work=[
            WorkModel(name="Software inc"),
            None,
        ]
    )

    user = User.from_pydantic(
        origin_user,
        extra={
            "work": [
                {"year": 2020},
                {"name": "Alternative", "year": 3030},
            ]
        },
    )

    assert user.work == [
        Work(name="Software inc", year=2020),
        # This was None in the UserModel
        Work(name="Alternative", year=3030),
    ]


def test_can_convert_pydantic_type_to_strawberry_with_optional_list():
    class WorkModel(BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto
        year: int

    class UserModel(BaseModel):
        work: Optional[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(work=None)

    user = User.from_pydantic(
        origin_user,
    )

    assert user.work is None


def test_can_convert_pydantic_type_to_strawberry_with_optional_nested_value():
    class UserModel(BaseModel):
        names: Optional[list[str]]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        names: strawberry.auto

    origin_user = UserModel(names=None)

    user = User.from_pydantic(
        origin_user,
    )

    assert user.names is None


def test_can_convert_input_types_to_pydantic():
    class User(BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto

    data = UserInput(age=1, password=None)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None


def test_can_convert_input_types_to_pydantic_default_values():
    class User(BaseModel):
        age: int
        password: Optional[str] = None

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto

    data = UserInput(age=1)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None


def test_can_convert_input_types_to_pydantic_default_values_defaults_declared_first():
    # test that we can declare a field with a default. before a field without a default
    class User(BaseModel):
        password: Optional[str] = None
        age: int

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        password: strawberry.auto
        age: strawberry.auto

    data = UserInput(age=1)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None

    definition: StrawberryObjectDefinition = UserInput.__strawberry_definition__
    assert definition.name == "UserInput"

    [
        password_field,
        age_field,
    ] = definition.fields

    assert age_field.python_name == "age"
    assert age_field.type is int

    assert password_field.python_name == "password"
    assert isinstance(password_field.type, StrawberryOptional)
    assert password_field.type.of_type is str


def test_can_convert_pydantic_type_to_strawberry_newtype():
    Password = NewType("Password", str)

    class User(BaseModel):
        age: int
        password: Optional[Password]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        password: strawberry.auto

    origin_user = User(age=1, password="abc")
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry_newtype_list():
    Password = NewType("Password", str)

    class User(BaseModel):
        age: int
        passwords: list[Password]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: strawberry.auto
        passwords: strawberry.auto

    origin_user = User(age=1, passwords=["hunter2"])
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.passwords == ["hunter2"]


def test_get_default_factory_for_field():
    class User(BaseModel):
        pass

    compat = PydanticCompat.from_model(User)
    MISSING_TYPE = compat.PYDANTIC_MISSING_TYPE

    def _get_field(
        default: Any = MISSING_TYPE,
        default_factory: Any = MISSING_TYPE,
    ) -> CompatModelField:
        return CompatModelField(
            name="a",
            type_=str,
            outer_type_=str,
            default=default,
            default_factory=default_factory,
            alias="a",
            allow_none=False,
            description="",
            has_alias=False,
            required=True,
            _missing_type=MISSING_TYPE,
            is_v1=not IS_PYDANTIC_V2,
        )

    field = _get_field()

    assert get_default_factory_for_field(field, compat) is dataclasses.MISSING

    def factory_func():
        return "strawberry"

    field = _get_field(default_factory=factory_func)

    # should return the default_factory unchanged
    assert get_default_factory_for_field(field, compat) is factory_func

    mutable_default = [123, "strawberry"]

    field = _get_field(mutable_default)

    created_factory = get_default_factory_for_field(field, compat)

    # should return a factory that copies the default parameter
    assert created_factory() == mutable_default
    assert created_factory() is not mutable_default

    field = _get_field(default=mutable_default, default_factory=factory_func)

    with pytest.raises(
        BothDefaultAndDefaultFactoryDefinedError,
        match=("Not allowed to specify both default and default_factory."),
    ):
        get_default_factory_for_field(field, compat)


def test_convert_input_types_to_pydantic_default_and_default_factory():
    # Pydantic should raise an error if the user specifies both default
    # and default_factory. this checks for a regression on their side
    if IS_PYDANTIC_V2:
        with pytest.raises(
            TypeError,
            match=("cannot specify both default and default_factory"),
        ):

            class User(BaseModel):
                password: Optional[str] = Field(
                    default=None, default_factory=lambda: None
                )

    else:
        with pytest.raises(
            ValueError,
            match=("cannot specify both default and default_factory"),
        ):

            class User(BaseModel):
                password: Optional[str] = Field(
                    default=None, default_factory=lambda: None
                )


def test_can_convert_pydantic_type_to_strawberry_with_additional_field_resolvers():
    def some_resolver() -> int:
        return 84

    class UserModel(BaseModel):
        password: Optional[str]
        new_age: int

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        password: strawberry.auto
        new_age: int = strawberry.field(resolver=some_resolver)

        @strawberry.field
        def age() -> int:
            return 42

    origin_user = UserModel(password="abc", new_age=21)
    user = User.from_pydantic(origin_user)
    assert user.password == "abc"
    assert User.__strawberry_definition__.fields[0].name == "age"
    assert User.__strawberry_definition__.fields[0].base_resolver() == 42
    assert User.__strawberry_definition__.fields[2].name == "new_age"
    assert User.__strawberry_definition__.fields[2].base_resolver() == 84


def test_can_convert_both_output_and_input_type():
    class Work(BaseModel):
        time: float

    class User(BaseModel):
        name: str
        work: Optional[Work]

    class Group(BaseModel):
        users: list[User]

    # Test both definition orders
    @strawberry.experimental.pydantic.input(Work)
    class WorkInput:
        time: strawberry.auto

    @strawberry.experimental.pydantic.type(Work)
    class WorkOutput:
        time: strawberry.auto

    @strawberry.experimental.pydantic.type(User)
    class UserOutput:
        name: strawberry.auto
        work: strawberry.auto

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        name: strawberry.auto
        work: strawberry.auto

    @strawberry.experimental.pydantic.input(Group)
    class GroupInput:
        users: strawberry.auto

    @strawberry.experimental.pydantic.type(Group)
    class GroupOutput:
        users: strawberry.auto

    origin_group = Group(
        users=[
            User(name="Alice", work=Work(time=10.0)),
            User(name="Bob", work=Work(time=5.0)),
        ]
    )
    group = GroupOutput.from_pydantic(origin_group)
    final_group = group.to_pydantic()
    assert origin_group == final_group

    group_input = GroupInput.from_pydantic(origin_group)
    final_group = group_input.to_pydantic()
    assert origin_group == final_group


def test_custom_conversion_functions():
    class User(BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: str
        password: strawberry.auto

        @staticmethod
        def from_pydantic(
            instance: User, extra: Optional[dict[str, Any]] = None
        ) -> "UserType":
            return UserType(
                age=str(instance.age),
                password=base64.b64encode(instance.password.encode()).decode()
                if instance.password
                else None,
            )

        def to_pydantic(self) -> User:
            return User(
                age=int(self.age),
                password=base64.b64decode(self.password.encode()).decode()
                if self.password
                else None,
            )

    user = User(age=1, password="abc")
    user_strawberry = UserType.from_pydantic(user)

    assert user_strawberry.age == "1"
    assert user_strawberry.password == "YWJj"

    user_pydantic = user_strawberry.to_pydantic()
    assert user == user_pydantic


def test_nested_custom_conversion_functions():
    class User(BaseModel):
        age: int
        password: Optional[str]

    class Parent(BaseModel):
        user: User

    @strawberry.experimental.pydantic.type(User)
    class UserType:
        age: str
        password: strawberry.auto

        @staticmethod
        def from_pydantic(
            instance: User, extra: Optional[dict[str, Any]] = None
        ) -> "UserType":
            return UserType(
                age=str(instance.age),
                password=base64.b64encode(instance.password.encode()).decode()
                if instance.password
                else None,
            )

        def to_pydantic(self) -> User:
            return User(
                age=int(self.age),
                password=base64.b64decode(self.password.encode()).decode()
                if self.password
                else None,
            )

    @strawberry.experimental.pydantic.type(Parent)
    class ParentType:
        user: strawberry.auto

    user = User(age=1, password="abc")
    parent = Parent(user=user)
    parent_strawberry = ParentType.from_pydantic(parent)

    assert parent_strawberry.user.age == "1"
    assert parent_strawberry.user.password == "YWJj"

    parent_pydantic = parent_strawberry.to_pydantic()
    assert parent == parent_pydantic


def test_can_convert_input_types_to_pydantic_with_non_pydantic_dataclass():
    @strawberry.type
    class Work:
        hours: int

    class User(BaseModel):
        age: int
        password: Optional[str]
        work: Work

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto
        work: strawberry.auto

    data = UserInput(age=1, password=None, work=Work(hours=1))
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None
    assert user.work.hours == 1


def test_can_convert_input_types_to_pydantic_with_dict():
    class Work(BaseModel):
        hours: int

    class User(BaseModel):
        age: int
        password: Optional[str]
        work: dict[str, Work]

    @strawberry.experimental.pydantic.input(Work)
    class WorkInput:
        hours: strawberry.auto

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto
        work: strawberry.auto

    data = UserInput(age=1, password=None, work={"Monday": Work(hours=1)})
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None
    assert user.work["Monday"].hours == 1


def test_can_add_missing_arguments_to_pydantic():
    class User(BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.type(User)
    class UserInput:
        age: strawberry.auto

    data = UserInput(age=1)
    user = data.to_pydantic(password="hunter2")

    assert user.age == 1
    assert user.password == "hunter2"


def test_raise_missing_arguments_to_pydantic():
    class User(BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.type(User)
    class UserInput:
        age: strawberry.auto

    data = UserInput(age=1)

    with pytest.raises(
        ValidationError,
        match=("1 validation error for User"),
    ):
        data.to_pydantic()


def test_can_convert_generic_alias_fields_to_strawberry():
    class TestModel(BaseModel):
        list_1d: list[int]
        list_2d: list[list[int]]

    @strawberry.experimental.pydantic.type(TestModel)
    class Test:
        list_1d: strawberry.auto
        list_2d: strawberry.auto

    fields = Test.__strawberry_definition__.fields
    assert isinstance(fields[0].type, StrawberryList)
    assert isinstance(fields[1].type, StrawberryList)

    model = TestModel(
        list_1d=[1, 2, 3],
        list_2d=[[1, 2], [3]],
    )
    test = Test.from_pydantic(model)

    assert test.list_1d == [1, 2, 3]
    assert test.list_2d == [[1, 2], [3]]


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="union type expressions were added in python 3.10",
)
def test_can_convert_optional_union_type_expression_fields_to_strawberry():
    class TestModel(BaseModel):
        optional_list: list[int] | None
        optional_str: str | None

    @strawberry.experimental.pydantic.type(TestModel)
    class Test:
        optional_list: strawberry.auto
        optional_str: strawberry.auto

    fields = Test.__strawberry_definition__.fields
    assert isinstance(fields[0].type, StrawberryOptional)
    assert isinstance(fields[1].type, StrawberryOptional)

    model = TestModel(
        optional_list=[1, 2, 3],
        optional_str=None,
    )
    test = Test.from_pydantic(model)

    assert test.optional_list == [1, 2, 3]
    assert test.optional_str is None


@needs_pydantic_v1
def test_can_convert_pydantic_type_to_strawberry_with_constrained_list():
    from pydantic import ConstrainedList

    class WorkModel(BaseModel):
        name: str

    class WorkList(ConstrainedList):
        min_items = 1

    class UserModel(BaseModel):
        work: WorkList[WorkModel]

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(
        work=[WorkModel(name="developer"), WorkModel(name="tester")]
    )

    user = User.from_pydantic(origin_user)

    assert user == User(work=[Work(name="developer"), Work(name="tester")])


SI = TypeVar("SI", covariant=True)  # pragma: no mutate


class SpecialList(list[SI]):
    pass


@needs_pydantic_v1
def test_can_convert_pydantic_type_to_strawberry_with_specialized_list():
    class WorkModel(BaseModel):
        name: str

    class WorkList(SpecialList[SI]):
        min_items = 1

    class UserModel(BaseModel):
        work: WorkList[WorkModel]

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(
        work=[WorkModel(name="developer"), WorkModel(name="tester")]
    )

    user = User.from_pydantic(origin_user)

    assert user == User(work=[Work(name="developer"), Work(name="tester")])

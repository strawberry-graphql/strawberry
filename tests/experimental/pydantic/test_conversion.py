from enum import Enum
from typing import List, Optional, Union

import pytest

import pydantic

import strawberry


def test_can_use_type_standalone():
    class User(pydantic.BaseModel):
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
    class User(pydantic.BaseModel):
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


def test_can_convert_alias_pydantic_field_to_strawberry():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age_: strawberry.auto
        password: strawberry.auto

    origin_user = UserModel(age=1, password="abc")
    user = User.from_pydantic(origin_user)

    assert user.age_ == 1
    assert user.password == "abc"


def test_can_convert_falsy_values_to_strawberry():
    class UserModel(pydantic.BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.auto

    origin_user = UserModel(age=0, password="")
    user = User.from_pydantic(origin_user)

    assert user.age == 0
    assert user.password == ""


def test_can_convert_pydantic_type_to_strawberry_with_private_field():
    class UserModel(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(model=UserModel)
    class User:
        age: strawberry.auto
        password: strawberry.Private[str]

    user = User(age=30, password="qwerty")
    assert user.age == 30
    assert user.password == "qwerty"

    definition = User._type_definition
    assert len(definition.fields) == 1
    assert definition.fields[0].python_name == "age"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == int


def test_can_convert_pydantic_type_with_nested_data_to_strawberry():
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: WorkModel

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: strawberry.auto

    origin_user = UserModel(work=WorkModel(name="Ice Cream inc"))
    user = User.from_pydantic(origin_user)

    assert user.work.name == "Ice Cream inc"


def test_can_convert_pydantic_type_with_list_of_nested_data_to_strawberry():
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

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
    class UserModel(pydantic.BaseModel):
        hours: List[int]

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
    class UserModel(pydantic.BaseModel):
        hours: List[List[int]]

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
    class HourModel(pydantic.BaseModel):
        hour: int

    @strawberry.experimental.pydantic.type(HourModel)
    class Hour:
        hour: strawberry.auto

    class UserModel(pydantic.BaseModel):
        hours: List[List[HourModel]]

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
    class BranchA(pydantic.BaseModel):
        field_a: str

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
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

    class User(pydantic.BaseModel):
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
    class BranchA(pydantic.BaseModel):
        field_a: str

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
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

    class User(pydantic.BaseModel):
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
    class Base(pydantic.BaseModel):
        base_field: str

    class BranchA(Base):
        field_a: str

    class BranchB(Base):
        field_b: int

    class User(pydantic.BaseModel):
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
    class UserModel(pydantic.BaseModel):
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

    class UserModel(pydantic.BaseModel):
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

    class UserModel(pydantic.BaseModel):
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        work: List[Work]
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
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        year: int
        name: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

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
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        year: int
        name: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: List[Optional[WorkModel]]

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
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel)
    class Work:
        name: strawberry.auto
        year: int

    class UserModel(pydantic.BaseModel):
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
    class UserModel(pydantic.BaseModel):
        names: Optional[List[str]]

    @strawberry.experimental.pydantic.type(UserModel)
    class User:
        names: strawberry.auto

    origin_user = UserModel(names=None)

    user = User.from_pydantic(
        origin_user,
    )

    assert user.names is None


def test_can_convert_input_types_to_pydantic():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto

    data = UserInput(1, None)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None


def test_can_convert_input_types_to_pydantic_default_values():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str] = None

    @strawberry.experimental.pydantic.input(User)
    class UserInput:
        age: strawberry.auto
        password: strawberry.auto

    data = UserInput(1)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None


def test_can_convert_pydantic_type_to_strawberry_error():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]
        name: pydantic.constr(min_length=5)

    @strawberry.experimental.pydantic.error_type(User)
    class UserError:
        age: strawberry.auto
        password: strawberry.auto
        name: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": "abc", "password": "abc", "name": "123"})

    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age == ["type_error.integer: value is not a valid integer"]
    assert user_error.password is None
    assert user_error.name == [
        "value_error.any_str.min_length: ensure this value has at least 5 characters"
    ]


def test_can_convert_alias_pydantic_field_to_strawberry_error():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age_: strawberry.auto
        password: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj({"age": "foo", "password": "abc"})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age_ == ["type_error.integer: value is not a valid integer"]
    assert user_error.password is None


def test_can_convert_falsy_values_to_strawberry_error():
    class UserModel(pydantic.BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        age: strawberry.auto
        password: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj({"age": "", "password": ""})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age == ["type_error.integer: value is not a valid integer"]
    assert user_error.password is None


def test_can_convert_pydantic_type_with_nested_data_to_strawberry_error():
    class WorkModel(pydantic.BaseModel):
        age: int
        location: pydantic.constr(min_length=2)

    @strawberry.experimental.pydantic.error_type(WorkModel)
    class WorkError:
        age: strawberry.auto
        location: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: WorkModel

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        work: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj({"work": {"age": "Ice Cream inc", "location": "a"}})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.work.age == ["type_error.integer: value is not a valid integer"]
    assert user_error.work.location == [
        "value_error.any_str.min_length: ensure this value has at least 2 characters"
    ]


def test_can_convert_pydantic_type_with_nested_data_alias_to_strawberry_error():
    class WorkModel(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.error_type(WorkModel)
    class WorkError:
        age: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work_: WorkModel = pydantic.Field(..., alias="work")

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        work_: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj({"work": {"age": "Ice Cream inc"}})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.work_.age == ["type_error.integer: value is not a valid integer"]


def test_can_convert_pydantic_type_with_list_of_nested_data_to_strawberry_error():
    class WorkModel(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.error_type(WorkModel)
    class WorkError:
        age: strawberry.auto

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        work: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj(
            {"work": [{"age": "Ice Cream inc"}, {"age": "Wall Street"}]}
        )
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.work[0].age == [
        "type_error.integer: value is not a valid integer",
    ]
    assert user_error.work[1].age == [
        "type_error.integer: value is not a valid integer"
    ]


def test_can_convert_pydantic_type_with_list_of_nested_int_to_strawberry_error():
    class UserModel(pydantic.BaseModel):
        hours: List[int]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        hours: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj({"hours": [8, "foo", 10, "bar", 11]})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.hours == [
        None,
        ["type_error.integer: value is not a valid integer"],
        None,
        ["type_error.integer: value is not a valid integer"],
    ]


def test_can_convert_pydantic_type_with_matrix_list_of_nested_int_to_strawberry_error():
    class UserModel(pydantic.BaseModel):
        hours: List[List[int]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        hours: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj(
            {
                "hours": [
                    [8, "foo"],
                    ["bar", "baz"],
                    [10, 12],
                ]
            }
        )
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.hours == [
        [None, ["type_error.integer: value is not a valid integer"]],
        [
            ["type_error.integer: value is not a valid integer"],
            ["type_error.integer: value is not a valid integer"],
        ],
    ]


def test_can_convert_pydantic_type_with_matrix_list_of_nested_model_to_error():
    class HourModel(pydantic.BaseModel):
        hour: int

    @strawberry.experimental.pydantic.error_type(HourModel)
    class HourError:
        hour: strawberry.auto

    class UserModel(pydantic.BaseModel):
        hours: List[List[HourModel]]

    @strawberry.experimental.pydantic.error_type(UserModel)
    class UserError:
        hours: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        UserModel.parse_obj(
            {"hours": [[{"hour": "foo"}, {"hour": "bar"}], [{"hour": "baz"}]]}
        )

    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.hours == [
        [
            HourError(hour=["type_error.integer: value is not a valid integer"]),
            HourError(hour=["type_error.integer: value is not a valid integer"]),
        ],
        [HourError(hour=["type_error.integer: value is not a valid integer"])],
    ]


def test_can_convert_pydantic_type_to_strawberry_error_with_union():
    class BranchA(pydantic.BaseModel):
        field_a: int

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
        age: int
        union_field: Union[BranchA, BranchB]

    @strawberry.experimental.pydantic.error_type(BranchA)
    class BranchAError:
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.error_type(BranchB)
    class BranchBError:
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.error_type(User)
    class UserError:
        age: strawberry.auto
        union_field: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": 1, "union_field": {"field_a": "abc"}})

    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age is None
    assert len(user_error.union_field) == 2
    assert isinstance(user_error.union_field[0], BranchBError)
    assert user_error.union_field[0].field_b == [
        "value_error.missing: field required",
    ]
    assert isinstance(user_error.union_field[1], BranchAError)
    assert user_error.union_field[1].field_a == [
        "type_error.integer: value is not a valid integer",
    ]

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": 1, "union_field": {"field_b": "abc"}})

    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age is None
    assert len(user_error.union_field) == 2
    assert isinstance(user_error.union_field[0], BranchBError)
    assert user_error.union_field[0].field_b == [
        "type_error.integer: value is not a valid integer",
    ]
    assert isinstance(user_error.union_field[1], BranchAError)
    assert user_error.union_field[1].field_a == [
        "value_error.missing: field required",
    ]


def test_can_convert_pydantic_type_to_strawberry_error_with_union_nullable():
    class BranchA(pydantic.BaseModel):
        field_a: int

    class BranchB(pydantic.BaseModel):
        field_b: int

    class User(pydantic.BaseModel):
        age: int
        union_field: Union[None, BranchA, BranchB]

    @strawberry.experimental.pydantic.error_type(BranchA)
    class BranchAError:
        field_a: strawberry.auto

    @strawberry.experimental.pydantic.error_type(BranchB)
    class BranchBError:
        field_b: strawberry.auto

    @strawberry.experimental.pydantic.error_type(User)
    class UserError:
        age: strawberry.auto
        union_field: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": 1, "union_field": {"field_a": "abc"}})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age is None
    assert len(user_error.union_field) == 2
    assert isinstance(user_error.union_field[0], BranchBError)
    assert user_error.union_field[0].field_b == [
        "value_error.missing: field required",
    ]
    assert isinstance(user_error.union_field[1], BranchAError)
    assert user_error.union_field[1].field_a == [
        "type_error.integer: value is not a valid integer",
    ]

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": 1, "union_field": {"field_b": "abc"}})

    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age is None
    assert len(user_error.union_field) == 2
    assert isinstance(user_error.union_field[0], BranchBError)
    assert user_error.union_field[0].field_b == [
        "type_error.integer: value is not a valid integer",
    ]
    assert isinstance(user_error.union_field[1], BranchAError)
    assert user_error.union_field[1].field_a == [
        "value_error.missing: field required",
    ]


def test_can_convert_pydantic_type_to_strawberry_error_with_enum():
    @strawberry.enum
    class UserKind(Enum):
        user = 0
        admin = 1

    class User(pydantic.BaseModel):
        age: int
        kind: UserKind

    @strawberry.experimental.pydantic.error_type(User)
    class UserError:
        age: strawberry.auto
        kind: strawberry.auto

    with pytest.raises(pydantic.ValidationError) as e:
        User.parse_obj({"age": 1, "kind": "foo"})
    user_error = UserError.from_pydantic_error(e.value)

    assert user_error.age is None
    assert user_error.kind == [
        "type_error.enum: value is not a valid enumeration member; permitted: 0, 1"
    ]

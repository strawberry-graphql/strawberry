from typing import List, Optional, Union

import pydantic

import strawberry


def test_can_use_type_standalone():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    user = UserType(age=1, password="abc")

    assert user.age == 1
    assert user.password == "abc"


def test_can_convert_pydantic_type_to_strawberry():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    origin_user = User(age=1, password="abc")
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.password == "abc"


def test_can_convert_alias_pydantic_field_to_strawberry():
    class UserModel(pydantic.BaseModel):
        age_: int = pydantic.Field(..., alias="age")
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["age_", "password"])
    class User:
        pass

    origin_user = UserModel(age=1, password="abc")
    user = User.from_pydantic(origin_user)

    assert user.age_ == 1
    assert user.password == "abc"


def test_can_convert_falsy_values_to_strawberry():
    class UserModel(pydantic.BaseModel):
        age: int
        password: str

    @strawberry.experimental.pydantic.type(UserModel, fields=["age", "password"])
    class User:
        pass

    origin_user = UserModel(age=0, password="")
    user = User.from_pydantic(origin_user)

    assert user.age == 0
    assert user.password == ""


def test_can_convert_pydantic_type_to_strawberry_with_private_field():
    class UserModel(pydantic.BaseModel):
        age: int

    @strawberry.experimental.pydantic.type(model=UserModel, fields=["age"])
    class User:
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

    @strawberry.experimental.pydantic.type(WorkModel, fields=["name"])
    class Work:
        pass

    class UserModel(pydantic.BaseModel):
        work: WorkModel

    @strawberry.experimental.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

    origin_user = UserModel(work=WorkModel(name="Ice Cream inc"))
    user = User.from_pydantic(origin_user)

    assert user.work.name == "Ice Cream inc"


def test_can_convert_pydantic_type_with_list_of_nested_data_to_strawberry():
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.experimental.pydantic.type(WorkModel, fields=["name"])
    class Work:
        pass

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(UserModel, fields=["hours"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(UserModel, fields=["hours"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(HourModel, fields=["hour"])
    class Hour:
        pass

    class UserModel(pydantic.BaseModel):
        hours: List[List[HourModel]]

    @strawberry.experimental.pydantic.type(UserModel, fields=["hours"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType:
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["age", "union_field"])
    class UserType:
        pass

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

    @strawberry.experimental.pydantic.type(User, fields=["age", "union_field"])
    class UserType:
        pass

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

    @strawberry.experimental.pydantic.type(BranchA, fields=["field_a"])
    class BranchAType:
        pass

    @strawberry.experimental.pydantic.type(BranchB, fields=["field_b"])
    class BranchBType:
        pass

    @strawberry.experimental.pydantic.type(User, fields=["age", "union_field"])
    class UserType:
        pass

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


def test_can_convert_pydantic_type_to_strawberry_with_additional_fields():
    class UserModel(pydantic.BaseModel):
        password: Optional[str]

    @strawberry.experimental.pydantic.type(UserModel, fields=["password"])
    class User:
        age: int

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

    @strawberry.experimental.pydantic.type(UserModel, fields=["password"])
    class User:
        work: Work

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

    @strawberry.experimental.pydantic.type(UserModel, fields=["password"])
    class User:
        work: List[Work]

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

    @strawberry.experimental.pydantic.type(WorkModel, fields=["name"])
    class Work:
        year: int

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(WorkModel, fields=["name"])
    class Work:
        year: int

    class UserModel(pydantic.BaseModel):
        work: List[Optional[WorkModel]]

    @strawberry.experimental.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

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

    @strawberry.experimental.pydantic.type(WorkModel, fields=["name"])
    class Work:
        year: int

    class UserModel(pydantic.BaseModel):
        work: Optional[WorkModel]

    @strawberry.experimental.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

    origin_user = UserModel(work=None)

    user = User.from_pydantic(
        origin_user,
    )

    assert user.work is None


def test_can_convert_pydantic_type_to_strawberry_with_optional_nested_value():
    class UserModel(pydantic.BaseModel):
        names: Optional[List[str]]

    @strawberry.experimental.pydantic.type(UserModel, fields=["names"])
    class User:
        pass

    origin_user = UserModel(names=None)

    user = User.from_pydantic(
        origin_user,
    )

    assert user.names is None


def test_can_convert_input_types_to_pydantic():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.experimental.pydantic.input(User, fields=["age", "password"])
    class UserInput:
        pass

    data = UserInput(1, None)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None


def test_can_convert_input_types_to_pydantic_default_values():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str] = None

    @strawberry.experimental.pydantic.input(User, fields=["age", "password"])
    class UserInput:
        pass

    data = UserInput(1)
    user = data.to_pydantic()

    assert user.age == 1
    assert user.password is None

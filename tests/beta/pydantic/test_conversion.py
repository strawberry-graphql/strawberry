from typing import List, Optional

import pydantic

import strawberry


def test_can_use_type_standalone():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    user = UserType(age=1, password="abc")

    assert user.age == 1
    assert user.password == "abc"


def test_can_covert_pydantic_type_to_strawberry():
    class User(pydantic.BaseModel):
        age: int
        password: Optional[str]

    @strawberry.beta.pydantic.type(User, fields=["age", "password"])
    class UserType:
        pass

    origin_user = User(age=1, password="abc")
    user = UserType.from_pydantic(origin_user)

    assert user.age == 1
    assert user.password == "abc"


def test_can_covert_pydantic_type_with_nested_data_to_strawberry():
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.beta.pydantic.type(WorkModel, fields=["name"])
    class Work(pydantic.BaseModel):
        pass

    class UserModel(pydantic.BaseModel):
        work: WorkModel

    @strawberry.beta.pydantic.type(UserModel, fields=["work"])
    class User:
        pass

    origin_user = UserModel(work=WorkModel(name="Ice Cream inc"))
    user = User.from_pydantic(origin_user)

    assert user.work.name == "Ice Cream inc"


def test_can_covert_pydantic_type_with_list_of_nested_data_to_strawberry():
    class WorkModel(pydantic.BaseModel):
        name: str

    @strawberry.beta.pydantic.type(WorkModel, fields=["name"])
    class Work(pydantic.BaseModel):
        pass

    class UserModel(pydantic.BaseModel):
        work: List[WorkModel]

    @strawberry.beta.pydantic.type(UserModel, fields=["work"])
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


def test_can_covert_pydantic_type_with_list_of_nested_int_to_strawberry():
    class UserModel(pydantic.BaseModel):
        hours: List[int]

    @strawberry.beta.pydantic.type(UserModel, fields=["hours"])
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


def test_can_covert_pydantic_type_with_matrix_list_of_nested_int_to_strawberry():
    class UserModel(pydantic.BaseModel):
        hours: List[List[int]]

    @strawberry.beta.pydantic.type(UserModel, fields=["hours"])
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


def test_can_covert_pydantic_type_with_matrix_list_of_nested_model_to_strawberry():
    class HourModel(pydantic.BaseModel):
        hour: int

    @strawberry.beta.pydantic.type(HourModel, fields=["hour"])
    class Hour:
        pass

    class UserModel(pydantic.BaseModel):
        hours: List[List[HourModel]]

    @strawberry.beta.pydantic.type(UserModel, fields=["hours"])
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

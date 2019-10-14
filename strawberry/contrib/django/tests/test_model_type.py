from typing import List

import pytest

import strawberry
from strawberry.contrib.django.tests.models import TestModel
from strawberry.contrib.django.type import model_type
from strawberry.graphql import execute


@pytest.mark.asyncio
async def test_model_type():
    @model_type(model=TestModel, fields="__all__")
    class TestModelType:
        @strawberry.field
        def extra_info(self, info) -> str:
            return "more info"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type(root, info) -> TestModelType:
            return TestModel(name="modeltype")

    schema = strawberry.Schema(query=Query)

    response = await execute(
        query="""
        query {
            modelType {
                name
                extraInfo
            }
        }
    """,
        schema=schema,
    )

    assert response.data["modelType"]["name"] == "modeltype"
    assert response.data["modelType"]["extraInfo"] == "more info"


@pytest.mark.asyncio
async def test_model_type_can_override_type_fields():
    @model_type(model=TestModel, fields=["name"])
    class TestModelType:
        @strawberry.field
        def name(self, info) -> str:
            return "joe"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type(root, info) -> TestModelType:
            return TestModel(name="modeltype")

    schema = strawberry.Schema(query=Query)

    response = await execute(
        query="""
        query {
            modelType {
                name
            }
        }
    """,
        schema=schema,
    )

    assert response.data["modelType"]["name"] == "joe"


@pytest.mark.asyncio
async def test_model_type_only_fields():
    @model_type(model=TestModel, fields=["name"])
    class TestModelType:
        pass

    assert "name" in TestModelType.field.fields
    assert "id" not in TestModelType.field.fields
    assert "secret" not in TestModelType.field.fields


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_type_list():
    @model_type(model=TestModel, fields="__all__")
    class TestModelType:
        @strawberry.field
        def extra_info(self, info) -> str:
            return "more info"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type_list(root, info) -> List[TestModelType]:
            return TestModel.objects.all()

    schema = strawberry.Schema(query=Query)

    TestModel.objects.create(name="modeltype")
    TestModel.objects.create(name="modeltype")
    TestModel.objects.create(name="modeltype")

    response = await execute(
        query="""
        query {
            modelTypeList {
                id
                name
                extraInfo
            }
        }
    """,
        schema=schema,
    )

    assert len(response.data["modelTypeList"]) == 3


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_input_type():
    @model_type(model=TestModel, fields="__all__")
    class TestModelType:
        extra: str

    @model_type(model=TestModel, is_input=True, fields="__all__")
    class TestModelInputType:
        pass

    @strawberry.type
    class Query:
        hello: str = "world"

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_test_model(self, info, test: TestModelInputType) -> TestModelType:
            name = getattr(test, "name")
            return TestModel.objects.create(name=name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    response = await execute(
        query="""
        mutation {
            createTestModel(test: {
                name: "Hello world"
            }) {
                id
                name
            }
        }
    """,
        schema=schema,
    )

    assert response.data["createTestModel"]["name"] == "Hello world"

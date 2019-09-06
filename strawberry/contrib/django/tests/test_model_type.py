from typing import List

import pytest

import strawberry
from strawberry.contrib.django.tests.models import TestModel
from strawberry.contrib.django.type import model_type
from strawberry.graphql import execute


@pytest.mark.asyncio
async def test_model_type():
    @model_type(model=TestModel)
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
@pytest.mark.django_db
async def test_model_type_list():
    @model_type(model=TestModel)
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

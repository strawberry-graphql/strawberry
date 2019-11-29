from typing import List

import pytest

import strawberry
from strawberry.contrib.django.tests.models import DummyModel
from strawberry.contrib.django.type import model_type
from strawberry.graphql import execute


@pytest.mark.asyncio
async def test_model_type():
    @model_type(model=DummyModel, fields="__all__")
    class DummyModelType:
        @strawberry.field
        def extra_info(self, info) -> str:
            return "more info"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type(root, info) -> DummyModelType:
            return DummyModel(name="modeltype")

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
async def test_model_type_meta():
    @model_type
    class DummyModelType:
        class Meta:
            model = DummyModel
            fields = "__all__"

        @strawberry.field
        def extra_info(self, info) -> str:
            return "more info"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type(root, info) -> DummyModelType:
            return DummyModel(name="modeltype")

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
    @model_type(model=DummyModel, fields=["name"])
    class DummyModelType:
        @strawberry.field
        def name(self, info) -> str:
            return "joe"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type(root, info) -> DummyModelType:
            return DummyModel(name="modeltype")

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
    @model_type(model=DummyModel, fields=["name"])
    class DummyModelType:
        pass

    assert "name" in DummyModelType.field.fields
    assert "id" not in DummyModelType.field.fields
    assert "secret" not in DummyModelType.field.fields


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_model_type_list():
    @model_type(model=DummyModel, fields="__all__")
    class DummyModelType:
        @strawberry.field
        def extra_info(self, info) -> str:
            return "more info"

    @strawberry.type
    class Query:
        @strawberry.field
        def model_type_list(root, info) -> List[DummyModelType]:
            return DummyModel.objects.all()

    schema = strawberry.Schema(query=Query)

    DummyModel.objects.create(name="modeltype")
    DummyModel.objects.create(name="modeltype")
    DummyModel.objects.create(name="modeltype")

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
    @model_type(model=DummyModel, fields="__all__")
    class DummyModelType:
        extra: str

    @model_type(model=DummyModel, is_input=True, fields="__all__")
    class DummyModelInputType:
        pass

    @strawberry.type
    class Query:
        hello: str = "world"

    @strawberry.type
    class Mutation:
        @strawberry.field
        def create_dummy_model(self, info, test: DummyModelInputType) -> DummyModelType:
            name = getattr(test, "name")
            return DummyModel.objects.create(name=name)

    schema = strawberry.Schema(query=Query, mutation=Mutation)

    print(dir(DummyModelInputType))

    response = await execute(
        query="""
        mutation {
            createDummyModel(test: {
                name: "Hello world"
            }) {
                id
                name
            }
        }
    """,
        schema=schema,
    )

    assert response.data["createDummyModel"]["name"] == "Hello world"

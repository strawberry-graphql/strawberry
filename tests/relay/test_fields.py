import dataclasses
import textwrap
from collections.abc import Iterable
from typing import Optional, Union
from typing_extensions import Self

import pytest
from pytest_mock import MockerFixture

import strawberry
from strawberry import relay
from strawberry.annotation import StrawberryAnnotation
from strawberry.relay.fields import ConnectionExtension
from strawberry.relay.utils import to_base64
from strawberry.schema.types.scalar import DEFAULT_SCALAR_REGISTRY
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.field import StrawberryField
from strawberry.types.fields.resolver import StrawberryResolver

from .schema import FruitAsync, schema


def test_query_node():
    result = schema.execute_sync(
        """
        query TestQuery ($id: GlobalID!) {
            node (id: $id) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "id": to_base64("Fruit", 2),
        },
    )
    assert result.errors is None
    assert result.data == {
        "node": {
            "id": to_base64("Fruit", 2),
            "color": "red",
            "name": "Apple",
        },
    }


async def test_query_node_with_async_permissions():
    result = await schema.execute(
        """
        query TestQuery ($id: GlobalID!) {
            nodeWithAsyncPermissions (id: $id) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "id": to_base64("Fruit", 2),
        },
    )
    assert result.errors is None
    assert result.data == {
        "nodeWithAsyncPermissions": {
            "id": to_base64("Fruit", 2),
            "color": "red",
            "name": "Apple",
        },
    }


def test_query_node_optional():
    result = schema.execute_sync(
        """
        query TestQuery ($id: GlobalID!) {
            nodeOptional (id: $id) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "id": to_base64("Fruit", 999),
        },
    )
    assert result.errors is None
    assert result.data == {"nodeOptional": None}


async def test_query_node_async():
    result = await schema.execute(
        """
        query TestQuery ($id: GlobalID!) {
            node (id: $id) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "id": to_base64("Fruit", 2),
        },
    )
    assert result.errors is None
    assert result.data == {
        "node": {
            "id": to_base64("Fruit", 2),
            "color": "red",
            "name": "Apple",
        },
    }


async def test_query_node_optional_async():
    result = await schema.execute(
        """
        query TestQuery ($id: GlobalID!) {
            nodeOptional (id: $id) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "id": to_base64("Fruit", 999),
        },
    )
    assert result.errors is None
    assert result.data == {"nodeOptional": None}


def test_query_nodes():
    result = schema.execute_sync(
        """
        query TestQuery ($ids: [GlobalID!]!) {
            nodes (ids: $ids) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "ids": [to_base64("Fruit", 2), to_base64("Fruit", 4)],
        },
    )
    assert result.errors is None
    assert result.data == {
        "nodes": [
            {
                "id": to_base64("Fruit", 2),
                "name": "Apple",
                "color": "red",
            },
            {
                "id": to_base64("Fruit", 4),
                "name": "Grape",
                "color": "purple",
            },
        ],
    }


def test_query_nodes_optional():
    result = schema.execute_sync(
        """
        query TestQuery ($ids: [GlobalID!]!) {
            nodesOptional (ids: $ids) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "ids": [
                to_base64("Fruit", 2),
                to_base64("Fruit", 999),
                to_base64("Fruit", 4),
            ],
        },
    )
    assert result.errors is None
    assert result.data == {
        "nodesOptional": [
            {
                "id": to_base64("Fruit", 2),
                "name": "Apple",
                "color": "red",
            },
            None,
            {
                "id": to_base64("Fruit", 4),
                "name": "Grape",
                "color": "purple",
            },
        ],
    }


async def test_query_nodes_async():
    result = await schema.execute(
        """
        query TestQuery ($ids: [GlobalID!]!) {
            nodes (ids: $ids) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
                ... on FruitAsync {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "ids": [
                to_base64("Fruit", 2),
                to_base64("Fruit", 4),
                to_base64("FruitAsync", 2),
            ],
        },
    )
    assert result.errors is None
    assert result.data == {
        "nodes": [
            {
                "id": to_base64("Fruit", 2),
                "name": "Apple",
                "color": "red",
            },
            {
                "id": to_base64("Fruit", 4),
                "name": "Grape",
                "color": "purple",
            },
            {
                "id": to_base64("FruitAsync", 2),
                "name": "Apple",
                "color": "red",
            },
        ],
    }


async def test_query_nodes_optional_async():
    result = await schema.execute(
        """
        query TestQuery ($ids: [GlobalID!]!) {
            nodesOptional (ids: $ids) {
                ... on Node {
                    id
                }
                ... on Fruit {
                    name
                    color
                }
                ... on FruitAsync {
                    name
                    color
                }
            }
        }
        """,
        variable_values={
            "ids": [
                to_base64("Fruit", 2),
                to_base64("FruitAsync", 999),
                to_base64("Fruit", 4),
                to_base64("Fruit", 999),
                to_base64("FruitAsync", 2),
            ],
        },
    )
    assert result.errors is None
    assert result.data == {
        "nodesOptional": [
            {
                "id": to_base64("Fruit", 2),
                "name": "Apple",
                "color": "red",
            },
            None,
            {
                "id": to_base64("Fruit", 4),
                "name": "Grape",
                "color": "purple",
            },
            None,
            {
                "id": to_base64("FruitAsync", 2),
                "name": "Apple",
                "color": "red",
            },
        ],
    }


fruits_query = """
query TestQuery (
    $first: Int = null
    $last: Int = null
    $before: String = null,
    $after: String = null,
) {{
    {} (
        first: $first
        last: $last
        before: $before
        after: $after
    ) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        edges {{
            cursor
            node {{
                id
                name
                color
            }}
        }}
    }}
}}
"""

attrs = [
    "fruits",
    "fruitsLazy",
    "fruitsAlias",
    "fruitsAliasLazy",
    "fruitsConcreteResolver",
    "fruitsCustomResolver",
    "fruitsCustomResolverLazy",
    "fruitsCustomResolverIterator",
    "fruitsCustomResolverIterable",
    "fruitsCustomResolverGenerator",
    "fruitAlikeConnectionCustomResolver",
]
async_attrs = [
    *attrs,
    "fruitsAsync",
    "fruitsCustomResolverAsyncIterator",
    "fruitsCustomResolverAsyncIterable",
    "fruitsCustomResolverAsyncGenerator",
]


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjQ=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "4"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_async(mocker, query_attr: str):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjQ=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "4"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection_filtering_first(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={"first": 2},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "1"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_filtering_first_async(mocker, query_attr: str):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={"first": 2},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "1"),
            },
        }
    }


def test_query_connection_filtering_after_without_first():
    result = schema.execute_sync(
        """{ someFruits {
            edges { node { id } }
            pageInfo {
                endCursor
            }
        } }"""
    )
    assert not result.errors
    assert len(result.data["someFruits"]["edges"]) == 100
    assert (
        relay.from_base64(result.data["someFruits"]["edges"][99]["node"]["id"])[1]
        == "99"
    )
    result = schema.execute_sync(
        """query ($after: String!){ someFruits(after: $after, first: 100) {
            edges { node { id } }
        } }""",
        variable_values={"after": result.data["someFruits"]["pageInfo"]["endCursor"]},
    )
    assert not result.errors
    assert len(result.data["someFruits"]["edges"]) == 100
    assert (
        relay.from_base64(result.data["someFruits"]["edges"][-1]["node"]["id"])[1]
        == "199"
    )


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection_filtering_first_with_after(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={"first": 2, "after": to_base64("arrayconnection", "1")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_filtering_first_with_after_async(
    mocker, query_attr: str
):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={"first": 2, "after": to_base64("arrayconnection", "1")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection_filtering_last(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={"last": 2},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjQ=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "3"),
                "endCursor": to_base64("arrayconnection", "4"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_filtering_last_async(mocker, query_attr: str):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={"last": 2},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjQ=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "3"),
                "endCursor": to_base64("arrayconnection", "4"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection_filtering_first_with_before(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={"first": 1, "before": to_base64("arrayconnection", "3")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "2"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_filtering_first_with_before_async(
    mocker, query_attr: str
):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={"first": 1, "before": to_base64("arrayconnection", "3")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "2"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", attrs)
def test_query_connection_filtering_last_with_before(query_attr: str):
    result = schema.execute_sync(
        fruits_query.format(query_attr),
        variable_values={"last": 2, "before": to_base64("arrayconnection", "4")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", async_attrs)
async def test_query_connection_filtering_last_with_before_async(
    mocker, query_attr: str
):
    mocker.patch.object(FruitAsync, "resolve_typename", return_value="Fruit")

    result = await schema.execute(
        fruits_query.format(query_attr),
        variable_values={"last": 2, "before": to_base64("arrayconnection", "4")},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


fruits_custom_query = """
query TestQuery (
    $first: Int = null
    $last: Int = null
    $before: String = null,
    $after: String = null,
) {
    fruitsCustomPagination (
        first: $first
        last: $last
        before: $before
        after: $after
    ) {
        something
        pageInfo {
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }
        edges {
            cursor
            node {
                id
                name
                color
            }
        }
    }
}
"""


def test_query_custom_connection():
    result = schema.execute_sync(
        fruits_custom_query,
        variable_values={},
    )
    assert result.errors is None
    assert result.data == {
        "fruitsCustomPagination": {
            "something": "foobar",
            "edges": [
                {
                    "cursor": "ZnJ1aXRfbmFtZTpBcHBsZQ==",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpCYW5hbmE=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpHcmFwZQ==",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpPcmFuZ2U=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpQaW5lYXBwbGU=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
            ],
            "pageInfo": {
                "startCursor": to_base64("fruit_name", "Apple"),
                "endCursor": to_base64("fruit_name", "Pineapple"),
                "hasNextPage": False,
                "hasPreviousPage": False,
            },
        }
    }


def test_query_custom_connection_filtering_first():
    result = schema.execute_sync(
        fruits_custom_query,
        variable_values={"first": 2},
    )
    assert result.errors is None
    assert result.data == {
        "fruitsCustomPagination": {
            "something": "foobar",
            "edges": [
                {
                    "cursor": "ZnJ1aXRfbmFtZTpBcHBsZQ==",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpCYW5hbmE=",
                    "node": {
                        "id": to_base64("Fruit", 1),
                        "color": "yellow",
                        "name": "Banana",
                    },
                },
            ],
            "pageInfo": {
                "startCursor": to_base64("fruit_name", "Apple"),
                "endCursor": to_base64("fruit_name", "Banana"),
                "hasNextPage": True,
                "hasPreviousPage": False,
            },
        }
    }


def test_query_custom_connection_filtering_first_with_after():
    result = schema.execute_sync(
        fruits_custom_query,
        variable_values={"first": 2, "after": to_base64("fruit_name", "Banana")},
    )
    assert result.errors is None
    assert result.data == {
        "fruitsCustomPagination": {
            "something": "foobar",
            "edges": [
                {
                    "cursor": "ZnJ1aXRfbmFtZTpHcmFwZQ==",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpPcmFuZ2U=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("fruit_name", "Grape"),
                "endCursor": to_base64("fruit_name", "Orange"),
            },
        }
    }


def test_query_custom_connection_filtering_last():
    result = schema.execute_sync(
        fruits_custom_query,
        variable_values={"last": 2},
    )
    assert result.errors is None
    assert result.data == {
        "fruitsCustomPagination": {
            "something": "foobar",
            "edges": [
                {
                    "cursor": "ZnJ1aXRfbmFtZTpPcmFuZ2U=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpQaW5lYXBwbGU=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": True,
                "startCursor": to_base64("fruit_name", "Orange"),
                "endCursor": to_base64("fruit_name", "Pineapple"),
            },
        }
    }


def test_query_custom_connection_filtering_last_with_before():
    result = schema.execute_sync(
        fruits_custom_query,
        variable_values={
            "last": 2,
            "before": to_base64("fruit_name", "Pineapple"),
        },
    )
    assert result.errors is None
    assert result.data == {
        "fruitsCustomPagination": {
            "something": "foobar",
            "edges": [
                {
                    "cursor": "ZnJ1aXRfbmFtZTpHcmFwZQ==",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "ZnJ1aXRfbmFtZTpPcmFuZ2U=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("fruit_name", "Grape"),
                "endCursor": to_base64("fruit_name", "Orange"),
            },
        }
    }


fruits_query_custom_resolver = """
query TestQuery (
    $first: Int = null
    $last: Int = null
    $before: String = null,
    $after: String = null,
    $nameEndswith: String = null
) {{
    {} (
        first: $first
        last: $last
        before: $before
        after: $after
        nameEndswith: $nameEndswith
    ) {{
        pageInfo {{
            hasNextPage
            hasPreviousPage
            startCursor
            endCursor
        }}
        edges {{
            cursor
            node {{
                id
                name
                color
            }}
        }}
    }}
}}
"""

custom_attrs = [
    "fruitsConcreteResolver",
    "fruitsCustomResolver",
    "fruitsCustomResolverIterator",
    "fruitsCustomResolverIterable",
    "fruitsCustomResolverGenerator",
    "fruitAlikeConnectionCustomResolver",
]
custom_async_attrs = [
    *attrs,
    "fruitsCustomResolverAsyncIterator",
    "fruitsCustomResolverAsyncIterable",
    "fruitsCustomResolverAsyncGenerator",
]


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_connection_custom_resolver(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"nameEndswith": "e"},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_connection_custom_resolver_filtering_first(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"first": 2, "nameEndswith": "e"},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjA=",
                    "node": {
                        "id": to_base64("Fruit", 2),
                        "color": "red",
                        "name": "Apple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": False,
                "startCursor": to_base64("arrayconnection", "0"),
                "endCursor": to_base64("arrayconnection", "1"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_connection_custom_resolver_filtering_first_with_after(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={
            "first": 2,
            "after": to_base64("arrayconnection", "1"),
            "nameEndswith": "e",
        },
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_connection_custom_resolver_filtering_last(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"last": 2, "nameEndswith": "e"},
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjM=",
                    "node": {
                        "id": to_base64("Fruit", 5),
                        "color": "orange",
                        "name": "Orange",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": False,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "2"),
                "endCursor": to_base64("arrayconnection", "3"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_connection_custom_resolver_filtering_last_with_before(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={
            "last": 2,
            "before": to_base64("arrayconnection", "3"),
            "nameEndswith": "e",
        },
    )
    assert result.errors is None
    assert result.data == {
        query_attr: {
            "edges": [
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjE=",
                    "node": {
                        "id": to_base64("Fruit", 3),
                        "color": "yellow",
                        "name": "Pineapple",
                    },
                },
                {
                    "cursor": "YXJyYXljb25uZWN0aW9uOjI=",
                    "node": {
                        "id": to_base64("Fruit", 4),
                        "color": "purple",
                        "name": "Grape",
                    },
                },
            ],
            "pageInfo": {
                "hasNextPage": True,
                "hasPreviousPage": True,
                "startCursor": to_base64("arrayconnection", "1"),
                "endCursor": to_base64("arrayconnection", "2"),
            },
        }
    }


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_first_negative(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"first": -1},
    )
    assert result.errors is not None
    assert (
        result.errors[0].message == "Argument 'first' must be a non-negative integer."
    )


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_first_higher_than_max_results(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"first": 500},
    )
    assert result.errors is not None
    assert result.errors[0].message == "Argument 'first' cannot be higher than 100."


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_last_negative(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"last": -1},
    )
    assert result.errors is not None
    assert result.errors[0].message == "Argument 'last' must be a non-negative integer."


@pytest.mark.parametrize("query_attr", custom_attrs)
def test_query_last_higher_than_max_results(query_attr: str):
    result = schema.execute_sync(
        fruits_query_custom_resolver.format(query_attr),
        variable_values={"last": 500},
    )
    assert result.errors is not None
    assert result.errors[0].message == "Argument 'last' cannot be higher than 100."


def test_parameters(mocker: MockerFixture):
    # Avoid E501 errors
    mocker.patch.object(
        DEFAULT_SCALAR_REGISTRY[relay.GlobalID],
        "description",
        "__GLOBAL_ID_DESC__",
    )

    class CustomField(StrawberryField):
        @property
        def arguments(self) -> list[StrawberryArgument]:
            return [
                *super().arguments,
                StrawberryArgument(
                    python_name="foo",
                    graphql_name=None,
                    type_annotation=StrawberryAnnotation(str),
                    default=None,
                ),
            ]

        @arguments.setter
        def arguments(self, value: list[StrawberryArgument]):
            cls = self.__class__
            return super(cls, cls).arguments.fset(self, value)

    @strawberry.type
    class Fruit(relay.Node):
        code: relay.NodeID[str]

    def resolver(info: strawberry.Info) -> list[Fruit]: ...

    @strawberry.type
    class Query:
        fruit: relay.ListConnection[Fruit] = relay.connection(
            resolver=resolver,
            extensions=[ConnectionExtension()],
        )
        fruit_custom_field: relay.ListConnection[Fruit] = CustomField(
            base_resolver=StrawberryResolver(resolver),
            extensions=[ConnectionExtension()],
        )

    schema = strawberry.Schema(query=Query)
    expected = '''
    type Fruit implements Node {
      """The Globally Unique ID of this object"""
      id: GlobalID!
    }

    """A connection to a list of items."""
    type FruitConnection {
      """Pagination data for this connection"""
      pageInfo: PageInfo!

      """Contains the nodes in this connection"""
      edges: [FruitEdge!]!
    }

    """An edge in a connection."""
    type FruitEdge {
      """A cursor for use in pagination"""
      cursor: String!

      """The item at the end of the edge"""
      node: Fruit!
    }

    """__GLOBAL_ID_DESC__"""
    scalar GlobalID @specifiedBy(url: "https://relay.dev/graphql/objectidentification.htm")

    """An object with a Globally Unique ID"""
    interface Node {
      """The Globally Unique ID of this object"""
      id: GlobalID!
    }

    """Information to aid in pagination."""
    type PageInfo {
      """When paginating forwards, are there more items?"""
      hasNextPage: Boolean!

      """When paginating backwards, are there more items?"""
      hasPreviousPage: Boolean!

      """When paginating backwards, the cursor to continue."""
      startCursor: String

      """When paginating forwards, the cursor to continue."""
      endCursor: String
    }

    type Query {
      fruit(
        """Returns the items in the list that come before the specified cursor."""
        before: String = null

        """Returns the items in the list that come after the specified cursor."""
        after: String = null

        """Returns the first n items from the list."""
        first: Int = null

        """Returns the items in the list that come after the specified cursor."""
        last: Int = null
      ): FruitConnection!
      fruitCustomField(
        foo: String!

        """Returns the items in the list that come before the specified cursor."""
        before: String = null

        """Returns the items in the list that come after the specified cursor."""
        after: String = null

        """Returns the first n items from the list."""
        first: Int = null

        """Returns the items in the list that come after the specified cursor."""
        last: Int = null
      ): FruitConnection!
    }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


before_after_test_query = """
query fruitsBeforeAfterTest (
    $before: String = null,
    $after: String = null,
) {
    fruits (
        before: $before
        after: $after
    ) {
        edges {
            cursor
            node {
                id
            }
        }
    }
}
"""


async def test_query_before_error():
    """Verify if the error raised on a non-existing before hash
    raises the correct error.
    """
    # with pytest.raises(ValueError):
    index = to_base64("Fake", 9292292)
    result = await schema.execute(
        before_after_test_query,
        variable_values={"before": index},
    )
    assert result.errors is not None
    assert "Argument 'before' contains a non-existing value" in str(result.errors)


def test_query_after_error():
    """Verify if the error raised on a non-existing before hash
    raises the correct error.
    """
    index = to_base64("Fake", 9292292)
    result = schema.execute_sync(
        before_after_test_query,
        variable_values={"after": index},
    )

    assert result.errors is not None
    assert "Argument 'after' contains a non-existing value" in str(result.errors)


@pytest.mark.parametrize(
    ("type_name", "should_have_name"),
    [("Fruit", False), ("PublicFruit", True)],
)
@pytest.mark.django_db(transaction=True)
def test_correct_model_returned(type_name: str, should_have_name: bool):
    @dataclasses.dataclass
    class FruitModel:
        id: str
        name: str

    fruits: dict[str, FruitModel] = {"1": FruitModel(id="1", name="Strawberry")}

    @strawberry.type
    class Fruit(relay.Node):
        id: relay.NodeID[int]

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: Optional[strawberry.Info] = None,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> Iterable[Optional[Union[Self, FruitModel]]]:
            return [fruits[nid] if required else fruits.get(nid) for nid in node_ids]

    @strawberry.type
    class PublicFruit(relay.Node):
        id: relay.NodeID[int]
        name: str

        @classmethod
        def resolve_nodes(
            cls,
            *,
            info: Optional[strawberry.Info] = None,
            node_ids: Iterable[str],
            required: bool = False,
        ) -> Iterable[Optional[Union[Self, FruitModel]]]:
            return [fruits[nid] if required else fruits.get(nid) for nid in node_ids]

    @strawberry.type
    class Query:
        node: relay.Node = relay.node()

    schema = strawberry.Schema(query=Query, types=[Fruit, PublicFruit])

    node_id = relay.to_base64(type_name, "1")
    result = schema.execute_sync(
        """
        query NodeQuery($id: GlobalID!) {
          node(id: $id) {
            __typename
            id
            ... on PublicFruit {
              name
            }
          }
        }
    """,
        {"id": node_id},
    )
    assert result.errors is None
    assert isinstance(result.data, dict)

    assert result.data["node"]["__typename"] == type_name
    assert result.data["node"]["id"] == node_id
    if should_have_name:
        assert result.data["node"]["name"] == "Strawberry"
    else:
        assert "name" not in result.data["node"]

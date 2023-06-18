import pytest

from strawberry.relay.utils import to_base64

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

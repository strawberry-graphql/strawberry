def test_query_with_fields_from_different_services(graphql_client):
    response = graphql_client.query(
        """{
        products {
            id
            name
            orders {
                id
                customerName
            }
        }
    }"""
    )

    assert not response.errors
    assert response.data == {
        "products": [
            {
                "id": "1",
                "name": "Mango Ice Cream",
                "orders": [{"id": "1", "customerName": "Marco"}],
            },
            {
                "id": "2",
                "name": "Strawberry Ice Cream",
                "orders": [{"id": "2", "customerName": "Patrick"}],
            },
        ]
    }


def test_query_with_field_that_requires_more_fields(graphql_client):
    response = graphql_client.query(
        """{
        products {
            code
        }
    }"""
    )

    assert not response.errors
    assert response.data == {
        "products": [
            {
                "code": "OrderService:Mango Ice Cream",
            },
            {"code": "OrderService:Strawberry Ice Cream"},
        ]
    }


def test_query_non_federation_field_on_one_service(graphql_client):
    response = graphql_client.query("""{ productsService }""")

    assert not response.errors
    assert response.data == {"productsService": "products"}

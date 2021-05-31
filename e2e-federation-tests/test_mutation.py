def test_mutation_on_one_service_with_return_data_from_others(graphql_client):
    response = graphql_client.query(
        """mutation {
        createProduct(name: "Chocolate Ice cream") {
            id
            name
            orders {
                customerName
            }
        }
    }"""
    )

    assert not response.errors
    assert response.data == {
        "createProduct": {
            "id": "500",
            "name": "Chocolate Ice cream",
            "orders": [{"customerName": "Ethan Winters"}],
        }
    }

import strawberry


def test_defining_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    definition = Node.__strawberry_definition__

    assert definition.name == "Node"
    assert len(definition.fields) == 1

    assert definition.fields[0].python_name == "id"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == strawberry.ID

    assert definition.is_interface


def test_implementing_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    definition = User.__strawberry_definition__

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "id"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].python_name == "name"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type is str

    assert definition.is_interface is False
    assert definition.interfaces == [Node.__strawberry_definition__]


def test_implementing_interface_twice():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    @strawberry.type
    class Person(Node):
        name: str

    definition = User.__strawberry_definition__

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "id"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].python_name == "name"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type is str

    assert definition.is_interface is False
    assert definition.interfaces == [Node.__strawberry_definition__]

    definition = Person.__strawberry_definition__

    assert definition.name == "Person"
    assert len(definition.fields) == 2

    assert definition.fields[0].python_name == "id"
    assert definition.fields[0].graphql_name is None
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].python_name == "name"
    assert definition.fields[1].graphql_name is None
    assert definition.fields[1].type is str

    assert definition.is_interface is False
    assert definition.interfaces == [Node.__strawberry_definition__]


def test_interfaces_can_implement_other_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.interface
    class UserNodeInterface(Node):
        id: strawberry.ID
        name: str

    @strawberry.type
    class Person(UserNodeInterface):
        id: strawberry.ID
        name: str

    assert UserNodeInterface.__strawberry_definition__.is_interface is True
    assert UserNodeInterface.__strawberry_definition__.interfaces == [
        Node.__strawberry_definition__
    ]

    definition = Person.__strawberry_definition__
    assert definition.is_interface is False
    assert definition.interfaces == [
        UserNodeInterface.__strawberry_definition__,
        Node.__strawberry_definition__,
    ]

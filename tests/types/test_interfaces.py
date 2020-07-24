import strawberry


def test_defining_interface():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    definition = Node._type_definition

    assert definition.name == "Node"
    assert len(definition.fields) == 1

    assert definition.fields[0].name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.is_interface


def test_implementing_interfaces():
    @strawberry.interface
    class Node:
        id: strawberry.ID

    @strawberry.type
    class User(Node):
        name: str

    definition = User._type_definition

    assert definition.name == "User"
    assert len(definition.fields) == 2

    assert definition.fields[0].name == "id"
    assert definition.fields[0].type == strawberry.ID

    assert definition.fields[1].name == "name"
    assert definition.fields[1].type == str

    assert definition.is_interface is False
    assert definition.interfaces == [Node._type_definition]

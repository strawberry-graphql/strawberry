from graphql import OperationType, parse

from strawberry.utils.operation import get_first_operation


def test_document_without_operation_definition_nodes():
    document = parse(
        """
        fragment Test on Query {
            hello
        }
        """
    )
    assert get_first_operation(document) is None


def test_single_operation_definition_node():
    document = parse(
        """
        query Operation1 {
            hello
        }
        """
    )
    node = get_first_operation(document)
    assert node is not None
    assert node.operation == OperationType.QUERY


def test_multiple_operation_definition_nodes():
    document = parse(
        """
        mutation Operation1 {
            hello
        }
        query Operation2 {
            hello
        }
        """
    )
    node = get_first_operation(document)
    assert node is not None
    assert node.operation == OperationType.MUTATION

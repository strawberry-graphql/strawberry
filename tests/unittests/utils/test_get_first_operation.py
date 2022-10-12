from graphql import OperationType, parse

from strawberry.utils.operation import get_first_operation


def test_document_without_operation_definition_notes():
    document = parse(
        """
        fragment Test on Query {
            hello
        }
    """
    )
    assert get_first_operation(document) is None


def test_single_operation_definition_note():
    document = parse(
        """
        query Operation1 {
            hello
        }
    """
    )
    assert get_first_operation(document) is not None
    assert get_first_operation(document).operation == OperationType.QUERY


def test_multiple_operation_definition_notes():
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
    assert get_first_operation(document) is not None
    assert get_first_operation(document).operation == OperationType.MUTATION

from typing_extensions import TypedDict

class addBookResultAddBook(TypedDict):
    id: str

class addBookResult(TypedDict):
    add_book: addBookResultAddBook

class addBookVariables(TypedDict):
    input: str

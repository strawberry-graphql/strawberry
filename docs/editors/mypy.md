# MYPY Plugin Setup

Mypy is a static type checker for Python 3 and Python 2.7. If you sprinkle your code with type annotations, mypy can type check your code and find common bugs.

## Installing and running mypy

Mypy requires Python 3.6 or later to run

```$ python3 -m pip install mypy```


Once mypy is installed, run it by using the mypy tool: 

* ```$ mypy program.py``` (Python 3)

* ```$ mypy --py2 program.py``` (Python 2)


This command makes mypy type check your program.py file and print out any errors it finds. Mypy will type check your code statically: this means that it will check for errors without ever running your code, just like a linter.

A function without type annotations is considered to be dynamically typed by mypy:

```python
def greeting(name):
    return 'Hello ' + name
```

By default, mypy will not type check dynamically typed functions. This means that with a few exceptions, mypy will not report any errors with regular unannotated Python.

You can teach mypy to detect these kinds of bugs by adding type annotations (also known as type hints).

This function is now statically typed: mypy can use the provided type hints to detect incorrect usages of the `greeting` function.

```python
def greeting(name: str) -> str:
    return 'Hello ' + name
```

If you are trying to type check Python 2 code, you can add type hints using a comment-based syntax instead of the Python 3 annotation syntax.

**Note**
You are always free to ignore the errors mypy reports and treat them as just warnings, if you so wish: mypy runs independently from Python itself.

# backport of (parts of) Python 3.10 inspect module

import ast
import inspect
import linecache
import re


class ClassFoundException(Exception):
    pass


class _ClassFinder(ast.NodeVisitor):
    def __init__(self, qualname):
        self.stack = []
        self.qualname = qualname

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.stack.append("<locals>")
        self.generic_visit(node)
        self.stack.pop()
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.stack.append(node.name)
        if self.qualname == ".".join(self.stack):
            # Return the decorator for the class if present
            if node.decorator_list:
                line_number = node.decorator_list[0].lineno
            else:
                line_number = node.lineno

            # decrement by one since lines starts with indexing by zero
            line_number -= 1
            raise ClassFoundException(line_number)
        self.generic_visit(node)
        self.stack.pop()


def findsource(object):
    """Return the entire source file and starting line number for an object.
    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of all the lines
    in the file and the line number indexes a line in that list.  An OSError
    is raised if the source code cannot be retrieved."""

    file = inspect.getsourcefile(object)
    if file:
        # Invalidate cache if needed.
        linecache.checkcache(file)
    else:
        file = inspect.getfile(object)
        # Allow filenames in form of "<something>" to pass through.
        # `doctest` monkeypatches `linecache` module to enable
        # inspection, so let `linecache.getlines` to be called.
        if not (file.startswith("<") and file.endswith(">")):
            raise OSError("source code not available")

    module = inspect.getmodule(object, file)
    if module:
        lines = linecache.getlines(file, module.__dict__)
    else:
        lines = linecache.getlines(file)
    if not lines:
        raise OSError("could not get source code")

    if inspect.ismodule(object):
        return lines, 0

    if inspect.isclass(object):
        qualname = object.__qualname__
        source = "".join(lines)
        tree = ast.parse(source)
        class_finder = _ClassFinder(qualname)
        try:
            class_finder.visit(tree)
        except ClassFoundException as e:
            line_number = e.args[0]
            return lines, line_number
        else:
            raise OSError("could not find class definition")

    if inspect.ismethod(object):
        object = object.__func__
    if inspect.isfunction(object):
        object = object.__code__
    if inspect.istraceback(object):
        object = object.tb_frame
    if inspect.isframe(object):
        object = object.f_code
    if inspect.iscode(object):
        if not hasattr(object, "co_firstlineno"):
            raise OSError("could not find function definition")
        lnum = object.co_firstlineno - 1
        pat = re.compile(
            r"^(\s*def\s)|(\s*async\s+def\s)|(.*(?<!\w)lambda(:|\s))|^(\s*@)"
        )
        while lnum > 0:
            try:
                line = lines[lnum]
            except IndexError:
                raise OSError("lineno is out of bounds")
            if pat.match(line):
                break
            lnum = lnum - 1
        return lines, lnum
    raise OSError("could not find code object")


def getsourcelines(object):
    """Return a list of source lines and starting line number for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a list of the lines
    corresponding to the object and the line number indicates where in the
    original source file the first line of code was found.  An OSError is
    raised if the source code cannot be retrieved."""
    object = inspect.unwrap(object)
    lines, lnum = findsource(object)

    if inspect.istraceback(object):
        object = object.tb_frame

    # for module or frame that corresponds to module, return all source lines
    if inspect.ismodule(object) or (
        inspect.isframe(object) and object.f_code.co_name == "<module>"
    ):
        return lines, 0
    else:
        return inspect.getblock(lines[lnum:]), lnum + 1

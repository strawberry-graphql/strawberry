from strawberry.utils.docstrings import Docstring


def test_trailing_spaces():
    docstring = Docstring(
        """
        Short description

        Long description.

        very long indeed
    """
    )
    assert (
        "Short description\n\nLong description.\n\nvery long indeed"
        == docstring.main_description
    )


def test_leading_spaces():
    docstring = Docstring(
        """


          A
        B
         C
    """
    )
    assert "  A\nB\n C" == docstring.main_description


def test_blank_after_short_description():
    with_blank = Docstring(
        """
        Short description

        Long description
    """
    )

    without_blank = Docstring(
        """
        Short description
        Long description
    """
    )

    without_long_description = Docstring(
        """
        Short description
    """
    )

    assert "Short description\n\nLong description" == with_blank.main_description
    assert "Short description\nLong description" == without_blank.main_description
    assert "Short description" == without_long_description.main_description


def test_epidoc_syntax():
    docstring = Docstring(
        """
        Epidoc syntax

        @param arg1: The first argument
        @param arg2: The second argument
    """
    )

    assert "Epidoc syntax" == docstring.main_description
    assert "The first argument" == docstring.child_description("arg1")
    assert "The second argument" == docstring.child_description("arg2")
    assert docstring.child_description("arg3") is None


def test_google_syntax():
    docstring = Docstring(
        """
        Google syntax

        Args:
            arg1: The first argument
            arg2 (str): The second argument

        Attributes:
            attr1: The first attribute
            attr2 (str): The second attribute
    """
    )

    assert "Google syntax" == docstring.main_description
    assert "The first argument" == docstring.child_description("arg1")
    assert "The second argument" == docstring.child_description("arg2")
    assert docstring.child_description("arg3") is None
    assert "The first attribute" == docstring.child_description("attr1")
    assert "The second attribute" == docstring.child_description("attr2")
    assert docstring.child_description("attr3") is None


def test_numpydoc_syntax():
    docstring = Docstring(
        """
        Numpydoc syntax

        Parameters
        ----------
        arg1 : int
               The first argument
        arg2: str, optional
              The second argument

        Attributes
        ----------
        attr1: int
               The first attribute
        attr2: str
               The second attribute
    """
    )

    assert "Numpydoc syntax" == docstring.main_description
    assert "The first argument" == docstring.child_description("arg1")
    assert "The second argument" == docstring.child_description("arg2")
    assert docstring.child_description("arg3") is None
    assert "The first attribute" == docstring.child_description("attr1")
    assert "The second attribute" == docstring.child_description("attr2")
    assert docstring.child_description("attr3") is None


def test_none_target():
    docstring = Docstring(None)
    assert docstring.main_description is None
    assert docstring.child_description("arg") is None
    assert docstring.attribute_docstring("attr") is None


def test_no_attribute_docstring():
    def x():
        """Foo"""

    docstring = Docstring(x)

    assert "Foo" == docstring.main_description
    assert {} == docstring.attribute_docstrings
    assert docstring.attribute_docstring("invalid") is None


def test_attribute_docstring():
    class W:
        w: int
        # No docstring here

    class WX(W):
        w: int
        """ WX.w """

        x: int
        """ WX.x """

    class WXY(WX):
        x: int = 12

        y = 56
        """ WXY.y """

    class WXYZ(WXY):
        y = 48
        """ WXYZ.y """

        z: int = 56
        """
        WXYZ.z

        With long description
        """

    w_docstring = Docstring(W)
    wx_docstring = Docstring(WX)
    wxy_docstring = Docstring(WXY)
    wxyz_docstring = Docstring(WXYZ)

    assert set() == w_docstring.attribute_docstrings.keys()
    assert {"w", "x"} == wx_docstring.attribute_docstrings.keys()
    assert {"w", "x", "y"} == wxy_docstring.attribute_docstrings.keys()
    assert {"w", "x", "y", "z"} == wxyz_docstring.attribute_docstrings.keys()

    assert w_docstring.attribute_docstring("w") is None
    assert "WX.w" == wx_docstring.attribute_docstring("w")
    assert "WX.w" == wxy_docstring.attribute_docstring("w")
    assert "WX.w" == wxyz_docstring.attribute_docstring("w")

    assert w_docstring.attribute_docstring("x") is None
    assert "WX.x" == wx_docstring.attribute_docstring("x")
    assert "WX.x" == wxy_docstring.attribute_docstring("x")
    assert "WX.x" == wxyz_docstring.attribute_docstring("x")

    assert w_docstring.attribute_docstring("y") is None
    assert wx_docstring.attribute_docstring("y") is None
    assert "WXY.y" == wxy_docstring.attribute_docstring("y")
    assert "WXYZ.y" == wxyz_docstring.attribute_docstring("y")

    assert w_docstring.attribute_docstring("z") is None
    assert wx_docstring.attribute_docstring("z") is None
    assert wxy_docstring.attribute_docstring("z") is None
    assert "WXYZ.z\n\nWith long description" == wxyz_docstring.attribute_docstring("z")


def test_docstring_inheritance():
    class Base:
        # No docstrings
        pass

    class W(Base):
        """
        class W
        """

    class WX(W):
        """
        Attributes:
            w (int): WX.w
            x (int): WX.x
        """

    class WXY(WX):
        """
        class WXY

        Attributes:
            x (int):
            y (int): WXY.y
        """

    class WXYZ(WXY):
        """
        class WXYZ

        Attributes:
            y (int): WXYZ.y
            z (int): WXYZ.z
        """

    base_docstring = Docstring(Base)
    w_docstring = Docstring(W)
    wx_docstring = Docstring(WX)
    wxy_docstring = Docstring(WXY)
    wxyz_docstring = Docstring(WXYZ)

    assert base_docstring.main_description is None
    assert "class W" == w_docstring.main_description
    assert wx_docstring.main_description is None
    assert "class WXY" == wxy_docstring.main_description
    assert "class WXYZ" == wxyz_docstring.main_description

    assert base_docstring.child_description("w") is None
    assert w_docstring.child_description("w") is None
    assert "WX.w" == wx_docstring.child_description("w")
    assert "WX.w" == wxy_docstring.child_description("w")
    assert "WX.w" == wxyz_docstring.child_description("w")

    assert base_docstring.child_description("x") is None
    assert w_docstring.child_description("x") is None
    assert "WX.x" == wx_docstring.child_description("x")
    assert "WX.x" == wxy_docstring.child_description("x")
    assert "WX.x" == wxyz_docstring.child_description("x")

    assert base_docstring.child_description("y") is None
    assert w_docstring.child_description("y") is None
    assert wx_docstring.child_description("y") is None
    assert "WXY.y" == wxy_docstring.child_description("y")
    assert "WXYZ.y" == wxyz_docstring.child_description("y")

    assert base_docstring.child_description("z") is None
    assert w_docstring.child_description("z") is None
    assert wx_docstring.child_description("z") is None
    assert wxy_docstring.child_description("z") is None
    assert "WXYZ.z" == wxyz_docstring.child_description("z")


def test_none():
    docstring = Docstring(None)
    assert docstring.main_description is None
    assert docstring.child_description("a") is None
    assert docstring.attribute_docstring("a") is None

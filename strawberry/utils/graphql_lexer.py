from typing import Any, ClassVar

from pygments import token
from pygments.lexer import RegexLexer


class GraphQLLexer(RegexLexer):
    """GraphQL Lexer for Pygments, used by the debug server."""

    name = "GraphQL"
    aliases: ClassVar[list[str]] = ["graphql", "gql"]
    filenames: ClassVar[list[str]] = ["*.graphql", "*.gql"]
    mimetypes: ClassVar[list[str]] = ["application/graphql"]

    tokens: ClassVar[dict[str, list[tuple[str, Any]]]] = {
        "root": [
            (r"#.*", token.Comment.Singline),
            (r"\.\.\.", token.Operator),
            (r'"[\u0009\u000A\u000D\u0020-\uFFFF]*"', token.String.Double),
            (
                r"(-?0|-?[1-9][0-9]*)(\.[0-9]+[eE][+-]?[0-9]+|\.[0-9]+|[eE][+-]?[0-9]+)",
                token.Number.Float,
            ),
            (r"(-?0|-?[1-9][0-9]*)", token.Number.Integer),
            (r"\$+[_A-Za-z][_0-9A-Za-z]*", token.Name.Variable),
            (r"[_A-Za-z][_0-9A-Za-z]+\s?:", token.Text),
            (r"(type|query|mutation|@[a-z]+|on|true|false|null)\b", token.Keyword.Type),
            (r"[!$():=@\[\]{|}]+?", token.Punctuation),
            (r"[_A-Za-z][_0-9A-Za-z]*", token.Keyword),
            (r"(\s|,)", token.Text),
        ]
    }


__all__ = ["GraphQLLexer"]

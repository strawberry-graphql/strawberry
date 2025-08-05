import pytest

from strawberry.http.parse_content_type import parse_content_type


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [  # type: ignore
        ("application/json", ("application/json", {})),
        ("", ("", {})),
        ("application/json; charset=utf-8", ("application/json", {"charset": "utf-8"})),
        (
            "application/json; charset=utf-8; boundary=foobar",
            ("application/json", {"charset": "utf-8", "boundary": "foobar"}),
        ),
        (
            "application/json; boundary=foobar; charset=utf-8",
            ("application/json", {"boundary": "foobar", "charset": "utf-8"}),
        ),
        (
            "application/json; boundary=foobar",
            ("application/json", {"boundary": "foobar"}),
        ),
        (
            "application/json; boundary=foobar; charset=utf-8; foo=bar",
            (
                "application/json",
                {"boundary": "foobar", "charset": "utf-8", "foo": "bar"},
            ),
        ),
        (
            'multipart/mixed; boundary="graphql"; subscriptionSpec=1.0, application/json',
            (
                "multipart/mixed",
                {
                    "boundary": "graphql",
                    "subscriptionspec": "1.0, application/json",
                },
            ),
        ),
    ],
)
async def test_parse_content_type(
    content_type: str,
    expected: tuple[str, dict[str, str]],
):
    assert parse_content_type(content_type) == expected

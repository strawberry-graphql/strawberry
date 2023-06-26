

from strawberry.http.temporal_response import TemporalResponse


def test_set_cookie():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks")
    assert response.headers["Set-Cookie"] == "strawberry=rocks; Path=/; Secure"


def test_set_two_cookies():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks")
    response.set_cookie("snek", "is_little")
    assert response.headers["Set-Cookie"] == [
        "strawberry=rocks; Path=/; Secure",
        "snek=is_little; Path=/; Secure",
    ]


def test_set_three_cookies():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks")
    response.set_cookie("snek", "is_little")
    response.set_cookie("cookie", "is_tasty")
    assert response.headers["Set-Cookie"] == [
        "strawberry=rocks; Path=/; Secure",
        "snek=is_little; Path=/; Secure",
        "cookie=is_tasty; Path=/; Secure",
    ]


def test_delete_cookie():
    response = TemporalResponse()
    response.delete_cookie("strawberry")
    assert response.headers["Set-Cookie"] == 'strawberry=""; Max-Age=0; Path=/; Secure'

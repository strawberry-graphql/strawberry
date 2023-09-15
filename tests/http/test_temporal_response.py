from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

from strawberry.http.temporal_response import TemporalResponse


def test_set_cookie():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks")
    assert response.headers["Set-Cookie"] == "strawberry=rocks; Path=/; Secure"


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


def test_set_cookie_secure_false():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", secure=False)
    assert response.headers["Set-Cookie"] == "strawberry=rocks; Path=/"


def test_set_cookie_httponly():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", httponly=True)
    assert (
        response.headers["Set-Cookie"] == "strawberry=rocks; HttpOnly; Path=/; Secure"
    )


def test_set_cookie_max_age():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", max_age=100)
    assert (
        response.headers["Set-Cookie"]
        == "strawberry=rocks; Max-Age=100; Path=/; Secure"
    )


def test_set_cookie_path():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", path="/graphql")
    assert response.headers["Set-Cookie"] == "strawberry=rocks; Path=/graphql; Secure"


def test_set_cookie_domain():
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", domain="strawberry.rocks")
    assert (
        response.headers["Set-Cookie"]
        == "strawberry=rocks; Domain=strawberry.rocks; Path=/; Secure"
    )


@pytest.mark.parametrize("samesite", ["strict", "lax", "none"])
def test_set_cookie_samesite(samesite):
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", samesite=samesite)
    assert (
        response.headers["Set-Cookie"]
        == f"strawberry=rocks; Path=/; SameSite={samesite}; Secure"
    )


@freeze_time("20300101 00:00:00")
def test_set_cookie_expires():
    one_day_later = datetime.now() + timedelta(days=1)
    seconds_in_a_day = 86400
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", expires=one_day_later)
    assert (
        response.headers["Set-Cookie"]
        == f"strawberry=rocks; Max-Age={seconds_in_a_day}; Path=/; Secure"
    )


@freeze_time("20300101 00:00:00")
def test_set_cookie_expires_with_timezone():
    one_day_later = datetime.now(tz=zoneinfo.ZoneInfo("Europe/Berlin")) + timedelta(
        days=1
    )
    seconds_in_a_day = 86400
    response = TemporalResponse()
    response.set_cookie("strawberry", "rocks", expires=one_day_later)
    assert (
        response.headers["Set-Cookie"]
        == f"strawberry=rocks; Max-Age={seconds_in_a_day}; Path=/; Secure"
    )


def test_delete_cookie():
    response = TemporalResponse()
    response.delete_cookie("strawberry")
    assert response.headers["Set-Cookie"] == 'strawberry=""; Max-Age=0; Path=/; Secure'

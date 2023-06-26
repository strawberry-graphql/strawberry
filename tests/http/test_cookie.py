from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from strawberry.http.cookie import generate_cookie_header_value


def test_set_cookie():
    assert (
        generate_cookie_header_value("strawberry", "rocks")
        == "strawberry=rocks; Path=/; Secure"
    )


def test_set_cookie_secure_false():
    assert (
        generate_cookie_header_value("strawberry", "rocks", secure=False)
        == "strawberry=rocks; Path=/"
    )


def test_set_cookie_httponly():
    assert (
        generate_cookie_header_value("strawberry", "rocks", httponly=True)
        == "strawberry=rocks; HttpOnly; Path=/; Secure"
    )


def test_set_cookie_max_age():
    assert (
        generate_cookie_header_value("strawberry", "rocks", max_age=100)
        == "strawberry=rocks; Max-Age=100; Path=/; Secure"
    )


def test_set_cookie_path():
    assert (
        generate_cookie_header_value("strawberry", "rocks", path="/graphql")
        == "strawberry=rocks; Path=/graphql; Secure"
    )


def test_set_cookie_domain():
    assert (
        generate_cookie_header_value("strawberry", "rocks", domain="strawberry.rocks")
        == "strawberry=rocks; Domain=strawberry.rocks; Path=/; Secure"
    )


@pytest.mark.parametrize("samesite", ["strict", "lax", "none"])
def test_set_cookie_samesite(samesite):
    assert (
        generate_cookie_header_value("strawberry", "rocks", samesite=samesite)
        == f"strawberry=rocks; Path=/; SameSite={samesite}; Secure"
    )


@freeze_time("20300101 00:00:00")
def test_set_cookie_expires():
    one_day_later = datetime.now() + timedelta(days=1)
    seconds_in_a_day = 86400
    assert (
        generate_cookie_header_value("strawberry", "rocks", expires=one_day_later)
        == f"strawberry=rocks; Max-Age={seconds_in_a_day}; Path=/; Secure"
    )

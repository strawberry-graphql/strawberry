import datetime
from http.cookies import SimpleCookie
from typing import Optional, Union
from typing_extensions import Literal

SameSite = Union[Literal["strict"], Literal["lax"], Literal["none"]]


def generate_cookie_header_value(
    key: str,
    value: str,
    max_age: Optional[int] = None,
    expires: Optional[datetime.datetime] = None,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = True,
    httponly: bool = False,
    samesite: Optional[SameSite] = None,
) -> str:
    cookie: SimpleCookie = SimpleCookie()

    cookie[key] = value

    if expires is not None:
        if expires.tzinfo is None:
            # We have a naive datetime
            expires = expires.replace(tzinfo=datetime.timezone.utc)
        delta = expires - datetime.datetime.now(tz=datetime.timezone.utc)
        # We just use the max_age logic
        max_age = max(0, delta.days * 86400 + delta.seconds)
    if max_age is not None:
        cookie[key]["max-age"] = max_age
    if domain is not None:
        cookie[key]["domain"] = domain

    cookie[key]["path"] = path
    cookie[key]["secure"] = secure
    cookie[key]["httponly"] = httponly

    if samesite is not None:
        cookie[key]["samesite"] = samesite

    return cookie.output(header="").strip()

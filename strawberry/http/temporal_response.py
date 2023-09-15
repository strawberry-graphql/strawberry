import datetime
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from typing import Dict, List, Optional, Union
from typing_extensions import Literal

SameSite = Literal["strict", "lax", "none"]


@dataclass
class TemporalResponse:
    status_code: int = 200
    headers: Dict[str, Union[str, List[str]]] = field(default_factory=dict)

    def set_cookie(
        self,
        key: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[datetime.datetime] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = True,
        httponly: bool = False,
        samesite: Optional[SameSite] = None,
    ) -> None:
        """Set a cookie in the response

        Parameters:
            key:
                The name of the cookie
            value:
                The value of the cookie
            max_age:
                Set the max age of the cookie in seconds
            expires:
                An expiration date of the cookie. It is assumed
                to be in UTC, if the datetime has no timezone information
            path:
                The path value of the cookie
            domain:
                The domain / host of the cookie
            secure:
                The secure flag of the cookie. This is by default True
            httponly:
                Sets the HttpOnly flag
            samesite:
                The value of the SameSite attribute
        """
        cookie: SimpleCookie = SimpleCookie()

        cookie[key] = value
        cookie[key]["path"] = path
        cookie[key]["secure"] = secure
        cookie[key]["httponly"] = httponly

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
        if samesite is not None:
            cookie[key]["samesite"] = samesite

        header_value = cookie.output(header="").strip()

        # It is possible to have multiple Set-Cookie headers
        # so we need to support multiple values per key by using
        # a list of strings (if more than one Set-Cookie header should
        # be present)
        if "Set-Cookie" in self.headers:
            if isinstance(self.headers["Set-Cookie"], list):
                self.headers["Set-Cookie"].append(header_value)
            else:
                self.headers["Set-Cookie"] = [self.headers["Set-Cookie"], header_value]
        else:
            self.headers["Set-Cookie"] = header_value

    def delete_cookie(
        self, key: str, path: str = "/", domain: Union[None, str] = None
    ) -> None:
        self.set_cookie(key, "", path=path, max_age=0, domain=domain)

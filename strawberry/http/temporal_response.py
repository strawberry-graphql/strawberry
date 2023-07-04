import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from .cookie import SameSite, generate_cookie_header_value


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
        header_value = generate_cookie_header_value(
            key,
            value,
            max_age=max_age,
            expires=expires,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )

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

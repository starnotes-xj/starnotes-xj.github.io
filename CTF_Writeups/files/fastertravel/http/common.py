import re
import string
from enum import Enum
from typing import Union, Optional


def url_decode(s: str) -> str:
    result = ""
    i = 0
    while i < len(s):
        if s[i] == "%":
            result += chr(int(s[i + 1:i + 3], 16))
            i += 3
        else:
            result += s[i]
            i += 1

    return result


def url_encode(s: str) -> str:
    allowed = string.ascii_letters + string.digits + "-_.!~*'();/?:@&=+$,#"
    return "".join(f"%{ord(c):02x}" if c not in allowed else c for c in s)


class Method(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"

    @classmethod
    def values(cls):
        if not hasattr(cls, "_values"):
            cls._values = set(method.value for method in cls)
        return cls._values


class StatusCode(Enum):
    OK = 200
    FOUND = 302
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    INTERNAL_SERVER_ERROR = 500

    def __str__(self):
        mappings = {
            StatusCode.OK: "OK",
            StatusCode.FOUND: "Found",
            StatusCode.BAD_REQUEST: "Bad Request",
            StatusCode.FORBIDDEN: "Forbidden",
            StatusCode.NOT_FOUND: "Not Found",
            StatusCode.METHOD_NOT_ALLOWED: "Method Not Allowed",
            StatusCode.INTERNAL_SERVER_ERROR: "Internal Error",
        }
        return f"{self.value} {mappings[self]}"


class CaseInsensitiveDict(dict[str, str]):
    def __setitem__(self, key: str, value: str) -> None:
        super().__setitem__(key.lower(), value)

    def __getitem__(self, key: str) -> str:
        return super().__getitem__(key.lower())

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key.lower())

    def __contains__(self, key: object) -> bool:
        if isinstance(key, str):
            return super().__contains__(key.lower())
        return False

    def get(self, key: str, default: Union[str, None] = None) -> Union[str, None]:
        return super().get(key.lower(), default)

    def pop(self, key: str, default: Union[str, None] = None) -> Union[str, None]:
        return super().pop(key.lower(), default)

    def update(self, *args, **kwargs) -> None:
        for key, value in dict(*args, **kwargs).items():
            self[key] = value

    def copy(self) -> 'CaseInsensitiveDict':
        return CaseInsensitiveDict(self)


def urlparse(url: str) -> tuple[Optional[str], str, Optional[int], Optional[str]]:
    match = re.match(r"(?P<scheme>https?)://", url)
    scheme = match.group("scheme") if match else None
    rest = url[len(scheme + "://"):] if scheme else url

    match = re.match(r"(?P<host_and_port>[^/?#]+)", rest)
    if not match:
        return None, "", None, None

    host_and_port = match.group("host_and_port").rsplit(":", 1)
    if len(host_and_port) == 2:
        host, port = host_and_port
        path = rest[len(f"{host}:{port}"):]
    else:
        host, port = host_and_port[0], None
        path = rest[len(host):]

    return scheme, host, int(port) if port else None, path

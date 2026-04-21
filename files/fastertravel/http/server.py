import socket
import asyncio
import functools

from pathlib import Path
from string import Template
from typing import Callable, Awaitable, Optional
from datetime import datetime

from http.common import url_encode, url_decode, Method, StatusCode, CaseInsensitiveDict


template_base_path = Path("templates").absolute()


class Request:
    raw_data: bytes
    method: Method
    path: str
    query: dict[str, str]
    headers: CaseInsensitiveDict
    body: Optional[bytes]

    _form_args: Optional[dict[str, str]] = None

    def __init__(self, data: bytes):
        self.raw_data = data

        self.query = {}
        self.headers = CaseInsensitiveDict()
        self.body = None

        self.parse()

    def parse(self):
        lines = self.raw_data.split(b"\r\n")

        first_line_tokens = [t for t in lines[0].decode().split(" ") if len(t) > 0]
        if len(first_line_tokens) != 3:
            raise ValueError("Invalid request line")

        method, path, http = first_line_tokens
        if http != "HTTP/1.1":
            raise ValueError("Invalid HTTP version")

        if method not in Method.values():
            raise ValueError("Invalid method")
        self.method = Method[method]

        if "?" in path:
            self.path, query_string = path.split("?", 1)
            for pair in query_string.split("&"):
                key, value = pair.split("=", 1)
                self.query[url_decode(key)] = url_decode(value)
        else:
            self.path = path

        header_lines = 1
        for line in lines[1:]:
            line = line.decode()
            header_lines += 1
            if line == "":
                break
            key, value = line.split(": ", 1)
            self.headers[key] = value

        if header_lines != len(lines):
            self.body = b"\r\n".join(lines[header_lines:])

    @property
    def form_args(self) -> dict[str, str]:
        if self.body is None:
            return {}
        if self._form_args is None:
            self._form_args = {url_decode(k): url_decode(v) for k, v in (pair.split("=", 1) for pair in self.body.decode().split("&"))}
        return self._form_args

    def __str__(self):
        res = self.method.value
        res += " " + self.path

        if self.query:
            res += "?" + "&".join(f"{url_encode(k)}={url_encode(v)}" for k, v in self.query.items())

        if self.body:
            res += f" ({len(self.body)}B body)"

        return res


class Response:
    status_code: StatusCode
    body: Optional[bytes]
    headers: CaseInsensitiveDict

    def __init__(self, status_code: StatusCode = StatusCode.OK, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None):
        self.status_code = status_code
        self.headers = CaseInsensitiveDict()
        if headers is not None:
            self.headers.update(headers)
        if body is not None:
            self.body = body if isinstance(body, bytes) else body.encode()
        else:
            self.body = None

        if self.body is not None:
            if content_type is None:
                content_type = "text/plain"
            self.headers["Content-Length"] = str(len(self.body))

        if content_type is not None:
            self.headers["Content-Type"] = content_type

    def __str__(self, include_body_preview: bool = True):
        response = f"HTTP/1.1 {self.status_code}\r\n"
        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"

        if self.body is not None and include_body_preview:
            response += "\r\n"
            response += "<<body>>"

        return response

    def encode(self, encoding="utf-8"):
        return self.__str__(include_body_preview=False).encode(encoding) + b"\r\n" + (self.body if self.body is not None else b"")

    def __bytes__(self):
        return self.encode()

    @classmethod
    def ok(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        return cls(StatusCode.OK, body, content_type)

    @classmethod
    def found(cls, location: str, headers: Optional[dict[str, str]] = None) -> "Response":
        if headers is None:
            headers = {}
        headers["Location"] = location
        return cls(StatusCode.FOUND, None, None, headers)

    @classmethod
    def bad_request(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        if body is None:
            body = "Bad Request"
        return cls(StatusCode.BAD_REQUEST, body, content_type, headers)

    @classmethod
    def forbidden(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        if body is None:
            body = "Access Denied"
        return cls(StatusCode.FORBIDDEN, body, content_type, headers)

    @classmethod
    def not_found(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        if body is None:
            body = "Not Found"
        return cls(StatusCode.NOT_FOUND, body, content_type, headers)

    @classmethod
    def method_not_allowed(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        if body is None:
            body = "Method Not Allowed"
        return cls(StatusCode.METHOD_NOT_ALLOWED, body, content_type, headers)

    @classmethod
    def internal_server_error(cls, body: Optional[bytes | str] = None, content_type: Optional[str] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        if body is None:
            body = "Internal Server Error"
        return cls(StatusCode.INTERNAL_SERVER_ERROR, body, content_type, headers)

    @classmethod
    def template(cls, name: str, parameters: Optional[dict[str, str]] = None, headers: Optional[dict[str, str]] = None) -> "Response":
        template_path = template_base_path / f"{name}.html"
        if not template_path.resolve().parent == template_base_path or not template_path.exists():
            return cls.internal_server_error()

        template = Template(template_path.read_text())
        body = template.safe_substitute(parameters or {})
        return cls.ok(body, "text/html", headers)


class Server:
    def __init__(self, bind: str, port: int, security_headers: Optional[dict[str, str]] = None):
        self.bind = bind
        self.port = port
        self.tasks: dict[int, asyncio.Task] = {}
        self.handlers: dict[str, Callable[[Request], Awaitable[Response]]] = {}

        if security_headers is None:
            self.security_headers = {}
            self.security_headers["Content-Security-Policy"] = "default-src 'self'; script-src 'none'; object-src 'none'; frame-ancestors 'self'; base-uri 'none';"
            self.security_headers["X-Content-Type-Options"] = "nosniff"
            self.security_headers["X-Frame-Options"] = "DENY"
            self.security_headers["X-XSS-Protection"] = "1; mode=block"
            self.security_headers["Referrer-Policy"] = "no-referrer"

    def __call__(self):
        try:
            asyncio.run(self.run())
        except KeyboardInterrupt:
            pass

    async def run(self):
        self.loop = asyncio.get_event_loop()
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.bind, self.port))
        server_socket.setblocking(False)
        server_socket.listen(8)
        print(f"[{datetime.now()}] INFO    Server running on {self.bind}:{self.port}")

        task_id = 0
        while True:
            client_socket = None
            try:
                client_socket, addr = await self.loop.sock_accept(server_socket)
                self.tasks[task_id] = self.loop.create_task(self.handle_request(client_socket, addr, task_id))
                task_id += 1
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break
                print(f'[{datetime.now()}] ERROR    "{e}"')
                continue

        for task in self.tasks.values():
            try:
                await task
                del self.tasks[task_id]
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break

        for task in self.tasks.values():
            try:
                task.cancel()
            except Exception as e:
                if isinstance(e, KeyboardInterrupt):
                    break

    async def handle_request(self, socket: socket.socket, addr, task_id: int):
        request = None
        response = None
        try:
            request_data = await self.loop.sock_recv(socket, 65536)
            request = Request(request_data)

            if request.path in self.handlers:
                response = await self.handlers[request.path](request)
            else:
                response = await self.not_found_handler(request)


        except ValueError as e:
            print(f'[{datetime.now()}] ERROR    "{e}"')
            response = Response.bad_request()

        except Exception as e:
            # if it is a ctrl-c, just exit
            if isinstance(e, KeyboardInterrupt):
                raise e

            import traceback
            traceback.print_exc()

        finally:
            try:
                if request:
                    if response is None:
                        response = Response.internal_server_error()
                    print(f'[{datetime.now()}] {addr[0]} "{request}" {response.status_code.value} {"-" if response.body is None else f"({len(response.body)}B)"}')
                    self.add_security_headers(response)
                    await self.loop.sock_sendall(socket, response.encode())
                    socket.close()
            finally:
                del self.tasks[task_id]


    async def not_found_handler(self, request: Request) -> Response:
        return Response.not_found()


    def handle(self, path: str, request_method: Optional[Method] = None):
        def decorator(func: Callable[[Request], Awaitable[Response]]):
            @functools.wraps(func)
            async def wrapper(request: Request) -> Response:
                if request_method and request.method != request_method:
                    return Response.method_not_allowed()
                return await func(request)

            self.handlers[path] = wrapper
            return func

        return decorator

    def get(self, path: str):
        return self.handle(path, Method.GET)

    def post(self, path: str):
        return self.handle(path, Method.POST)

    def add_security_headers(self, response: Response) -> Response:
        for header, value in self.security_headers.items():
            if header not in response.headers:
                response.headers[header] = value
        return response


def force_iframe(func):
    @functools.wraps(func)
    async def wrapper(request: Request) -> Response:
        if "sec-fetch-dest" not in request.headers or request.headers["sec-fetch-dest"] != "iframe":
            return Response.forbidden("Access only possible in an iframe!")
        if "sec-fetch-site" not in request.headers or request.headers["sec-fetch-site"] != "same-origin":
            return Response.forbidden("Access only possible in an iframe!")

        res = await func(request)

        res.headers["X-Frame-Options"] = "SAMEORIGIN"
        return res

    return wrapper

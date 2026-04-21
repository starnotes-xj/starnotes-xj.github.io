import socket
import asyncio

from typing import Optional, Literal

from http.common import urlparse, url_encode


Method = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT"]


class Requester:
    async def request(self, method: Method, url: str, body: Optional[bytes] = None, verbose: bool = False) -> bytes:
        scheme, hostname, port, path = urlparse(url)
        if scheme not in ("http", "https"):
            raise ValueError("Scheme not supported")

        port = port or (443 if scheme == "https" else 80)
        path = url_encode(path) if path else "/"

        loop = asyncio.get_event_loop()
        try:
            addrs = await loop.getaddrinfo(hostname, port, family=socket.AF_INET, type=socket.SOCK_STREAM)
            if not addrs:
                raise ValueError("No address found")
        except socket.gaierror:
            raise ValueError("Address resolution failed")

        family, socktype, proto, canonname, sockaddr = addrs[0]

        try:
            if scheme == "https":
                reader, writer = await asyncio.open_connection(sockaddr[0], sockaddr[1], server_hostname=hostname, ssl=True)
            else:
                reader, writer = await asyncio.open_connection(sockaddr[0], sockaddr[1])
        except ConnectionRefusedError:
            raise ValueError("Connection refused")

        try:
            req = (
                f"{method} {path} HTTP/1.1\r\n"
                f"Host: {hostname}\r\n"
                f"User-Agent: fasttravel/0.1\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("utf-8")
            if body:
                req += body

            writer.write(req)
            await writer.drain()

            response = b""
            while True:
                chunk = await reader.read(4096)
                if not chunk:
                    break
                response += chunk

            if verbose:
                return response
        except:
            raise ValueError("Request failed")

        return self.parse(response)

    def parse(self, response: bytes) -> bytes:
        return response.split(b"\r\n\r\n", 1)[1]  # should be good enough for our usecase

    async def get(self, url: str) -> bytes:
        return await self.request("GET", url)

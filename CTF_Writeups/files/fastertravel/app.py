import os
import random
import string
import asyncio

from datetime import datetime, timedelta

from lru import LRUDict
from http.common import urlparse, Method
from http.client import Requester
from http.server import Server, Request, Response, force_iframe


FLAG = os.getenv("FLAG", "dach2026{dummy_flag}")
SHORTEN_RATE_LIMIT = timedelta(seconds=int(os.getenv("SHORTEN_RATE_LIMIT_SECONDS", 5)))


server = Server("127.0.0.1", 5001)


shortens: LRUDict[str, tuple[str, bytes]] = LRUDict(32)
last_shorten = datetime.now() - SHORTEN_RATE_LIMIT


PRIVILEGED_ORIGINS = ("localhost", "localhost:5000")


def privileged_origin_access(host: str) -> bool:
    return host in PRIVILEGED_ORIGINS


@server.get("/")
@server.get("/index")
async def index(request: Request) -> Response:
    return Response.template("index")


@server.get("/admin")
async def admin(request: Request) -> Response:
    if not privileged_origin_access(request.headers.get('Host', '')):
        return Response.forbidden()

    return Response.ok(f"Welcome to the secret admin panel! Flag: {FLAG}")


@server.get("/preview")
@force_iframe
async def preview(request: Request) -> Response:
    short = request.query.get('short')
    if not short:
        return Response.bad_request()

    if short not in shortens:
        return Response.not_found()

    return Response.ok(shortens[short][1], content_type="text/html")


@server.post("/shorten")
async def shorten(request: Request) -> Response:
    if "source" not in request.form_args:
        return Response.bad_request()

    url = request.form_args["source"]
    scheme, hostname, port, path = urlparse(url)
    if privileged_origin_access(hostname) or any(hostname.startswith(e) for e in PRIVILEGED_ORIGINS) or any(hostname.endswith(e) for e in PRIVILEGED_ORIGINS):  # just to be sure
        return Response.forbidden()

    global last_shorten
    if SHORTEN_RATE_LIMIT and (datetime.now() - last_shorten) < SHORTEN_RATE_LIMIT:
        print(f"[{datetime.now()}] WARN    Rate limiting shorten")
        to_sleep = (last_shorten + SHORTEN_RATE_LIMIT - datetime.now())
        last_shorten = datetime.now() + to_sleep
        await asyncio.sleep(to_sleep.total_seconds())
    else:
        last_shorten = datetime.now()

    short = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    try:
        preview = await Requester().get(url)
        if len(preview) > 2**20:
            print(f"[{datetime.now()}] WARN    preview is too large, truncating", len(preview), "to", 2**20)
            preview = preview[:2**16]
    except ConnectionRefusedError:
        return Response.bad_request("Invalid URL")
    shortens[short] = (url, preview)

    return Response.found(f"/{short}")


async def handle_resolve(request: Request) -> Response:
    if request.method != Method.GET:
        return Response.not_found()

    short = request.path[1:]
    if short in shortens:
        return Response.template("preview", {"url":shortens[short][0], "short": short})
    return Response.not_found()


server.not_found_handler = handle_resolve


if __name__ == "__main__":
    server()

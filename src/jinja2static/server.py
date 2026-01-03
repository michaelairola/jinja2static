from pathlib import Path
from asyncio import (
    CancelledError,
    StreamReader,
    StreamWriter,
    start_server,
)
from asyncio.exceptions import CancelledError
import logging
import traceback
import mimetypes

from .config import Config
from .watcher import file_watcher

logger = logging.getLogger(__name__)


async def receive_http_get_request(reader: StreamReader):
    request_data = b""
    while True:
        line = await reader.readline()
        if not line:
            # EOF reached without completing headers
            break
        request_data += line
        if line == b"\r\n":
            # Found the end of headers
            break
    headers = request_data.decode().split("\r\n")
    method, uri, _ = headers.pop(0).split(" ")
    return method, uri


def read_file(config: Config, file_path: Path) -> tuple[bytes, str]:
    assert file_path.is_relative_to(config.dist.resolve()), (
        f"File '{file_path}' is not located in distribution directory '{config.dist}'"
    )
    logger.debug(f"reading file {file_path}")
    mime_type, _ = mimetypes.guess_type(file_path.name)
    with open(file_path, "rb" if mime_type == "font/woff2" else "r") as file:
        file_data = file.read()
    file_data = file_data.encode("utf-8") if mime_type != "font/woff2" else file_data
    return file_data, mime_type


async def send_http_response(
    writer: StreamWriter,
    response_body: bytes,
    status: int = 200,
    content_type: str = "text/plain",
):
    response_header = (
        f"HTTP/1.1 {status} OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        f"\r\n"
    )
    writer.write(response_header.encode("utf-8"))
    writer.write(response_body)
    await writer.drain()


def configure_requestor(config: Config):
    async def handle_request(reader: StreamReader, writer: StreamWriter):
        try:
            method, uri = await receive_http_get_request(reader)
            # TODO make more robust, parse URI with urllib.
            uri = uri.removeprefix("/")
            uri = uri or "index.html"
            FILE_PATH = (config.dist / uri).resolve()

            if FILE_PATH.name == "500.html":
                raise Exception(
                    "Internal Server Test",
                    "This should always return an 500 internal server error.",
                )
            assert method == "GET", (
                "This is a Static server! You can only make GET requests."
            )
            assert FILE_PATH.is_file(), f"No File '{FILE_PATH}' found."

            response_body, mime_type = read_file(config, FILE_PATH)
            await send_http_response(writer, response_body, content_type=mime_type)
        except AssertionError as e:
            response_body = ",".join(e.args)
            await send_http_response(writer, response_body.encode("utf-8"), status=400)
        except Exception as e:
            response_body = "\n".join(
                ["EXCEPTION:", *e.args, "-" * 40, traceback.format_exc()]
            )
            logger.info(response_body)
            await send_http_response(writer, response_body.encode("utf-8"), status=500)
        finally:
            writer.close()
            await writer.wait_closed()

    return handle_request


async def server(port: int, config: Config | None):
    try:
        if not config:
            return
        file_watcher(config)
        handle_request = configure_requestor(config)
        server = await start_server(handle_request, "127.0.0.1", port)
        logger.info(f"Serving on port {port}")
        async with server:
            await server.serve_forever()
    except CancelledError:
        pass

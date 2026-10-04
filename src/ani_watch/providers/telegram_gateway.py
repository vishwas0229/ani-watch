"""Local HTTP gateway that streams Telegram media to VLC on demand."""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass
from urllib.parse import unquote, urlparse


@dataclass(frozen=True, slots=True)
class TelegramStreamHandle:
    """Metadata for one registered Telegram media message."""

    token: str
    message: object
    size: int
    mime_type: str
    filename: str


class TelegramStreamingGateway:
    """Expose authorized Telegram media through a local HTTP Range endpoint."""

    def __init__(
        self,
        client,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        chunk_size: int = 512 * 1024,
    ) -> None:
        self.client = client
        self.host = host
        self.port = port
        self.chunk_size = max(64 * 1024, int(chunk_size))
        self._server: asyncio.AbstractServer | None = None
        self._handles: dict[str, TelegramStreamHandle] = {}

    async def start(self) -> None:
        """Start the local HTTP listener once."""
        if self._server is not None:
            return
        self._server = await asyncio.start_server(
            self._handle_client,
            host=self.host,
            port=self.port,
        )

    async def close(self) -> None:
        """Stop the listener and forget registered media handles."""
        self._handles.clear()
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    @property
    def base_url(self) -> str:
        """Return the listener's local base URL."""
        if self._server is None:
            raise RuntimeError("Telegram streaming gateway is not started.")
        sockets = self._server.sockets or ()
        if not sockets:
            raise RuntimeError("Telegram streaming gateway has no listening socket.")
        address = sockets[0].getsockname()
        return f"http://{address[0]}:{address[1]}"

    def register(
        self,
        message,
        *,
        size: int,
        mime_type: str,
        filename: str,
    ) -> str:
        """Register a Telegram message and return its local playback URL."""
        token = secrets.token_urlsafe(24)
        self._handles[token] = TelegramStreamHandle(
            token=token,
            message=message,
            size=max(0, int(size)),
            mime_type=mime_type or "application/octet-stream",
            filename=filename or "media",
        )
        return f"{self.base_url}/telegram/{token}"

    @staticmethod
    def _parse_range(value: str | None, size: int) -> tuple[int, int] | None:
        """Parse a single HTTP byte range, returning inclusive start/end."""
        if not value:
            return None
        prefix, separator, spec = value.partition("=")
        if prefix.strip().lower() != "bytes" or not separator or "," in spec:
            raise ValueError("Only a single bytes range is supported.")
        start_text, dash, end_text = spec.strip().partition("-")
        if not dash:
            raise ValueError("Invalid byte range.")
        if not start_text:
            suffix = int(end_text)
            if suffix <= 0:
                raise ValueError("Invalid suffix byte range.")
            if size <= 0:
                raise ValueError("Requested range is outside the media.")
            start = max(0, size - suffix)
            end = size - 1
        else:
            start = int(start_text)
            end = int(end_text) if end_text else size - 1
            if start < 0 or start >= size or end < start:
                raise ValueError("Requested range is outside the media.")
            end = min(end, size - 1)
        if size <= 0 or start >= size:
            raise ValueError("Requested range is outside the media.")
        return start, end

    @staticmethod
    def _headers(
        status: str,
        *,
        content_type: str,
        content_length: int,
        size: int,
        start: int | None = None,
        end: int | None = None,
    ) -> bytes:
        lines = [
            f"HTTP/1.1 {status}",
            f"Content-Type: {content_type}",
            f"Content-Length: {content_length}",
            "Accept-Ranges: bytes",
            "Cache-Control: no-store",
            "Connection: close",
        ]
        if start is not None and end is not None:
            lines.append(f"Content-Range: bytes {start}-{end}/{size}")
        return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii", "strict")

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """Handle one VLC HTTP request and stream only the requested byte range."""
        response_started = False
        try:
            request_line = await asyncio.wait_for(reader.readline(), timeout=10)
            if not request_line:
                return
            parts = request_line.decode("latin-1").strip().split()
            if len(parts) != 3:
                await self._write_status(writer, "400 Bad Request")
                return

            method, target, _ = parts
            headers: dict[str, str] = {}
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=10)
                if not line or line in (b"\r\n", b"\n"):
                    break
                name, separator, value = line.decode("latin-1").partition(":")
                if separator:
                    headers[name.strip().lower()] = value.strip()

            parsed = urlparse(target)
            segments = [unquote(item) for item in parsed.path.split("/") if item]
            if len(segments) != 2 or segments[0] != "telegram":
                await self._write_status(writer, "404 Not Found")
                return

            handle = self._handles.get(segments[1])
            if handle is None:
                await self._write_status(writer, "404 Not Found")
                return

            if method not in {"GET", "HEAD"}:
                await self._write_status(
                    writer,
                    "405 Method Not Allowed",
                    extra=b"Allow: GET, HEAD\r\n",
                )
                return

            try:
                requested = self._parse_range(headers.get("range"), handle.size)
            except (TypeError, ValueError):
                error_headers = (
                    f"HTTP/1.1 416 Range Not Satisfiable\r\n"
                    f"Content-Range: bytes */{handle.size}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii")
                writer.write(error_headers)
                await writer.drain()
                return

            if requested is None:
                status = "200 OK"
                start, end = 0, max(0, handle.size - 1)
            else:
                status = "206 Partial Content"
                start, end = requested

            length = max(0, end - start + 1) if handle.size else 0
            response_started = True
            writer.write(
                self._headers(
                    status,
                    content_type=handle.mime_type,
                    content_length=length,
                    size=handle.size,
                    start=start if requested else None,
                    end=end if requested else None,
                )
            )
            await writer.drain()

            if method == "HEAD" or length == 0:
                return

            sent = 0
            chunks = (length + self.chunk_size - 1) // self.chunk_size
            async for chunk in self.client.iter_download(
                handle.message,
                offset=start,
                limit=chunks,
                chunk_size=self.chunk_size,
                request_size=self.chunk_size,
                file_size=handle.size,
            ):
                if not chunk:
                    continue
                remaining = length - sent
                data = chunk[:remaining]
                writer.write(data)
                await writer.drain()
                sent += len(data)
                if sent >= length:
                    break
        except (ConnectionError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        except asyncio.CancelledError:
            raise
        except Exception:
            if not response_started:
                try:
                    await self._write_status(writer, "502 Bad Gateway")
                except Exception:
                    pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    @staticmethod
    async def _write_status(
        writer: asyncio.StreamWriter,
        status: str,
        *,
        extra: bytes = b"",
    ) -> None:
        writer.write(
            f"HTTP/1.1 {status}\r\nConnection: close\r\n{extra.decode('latin-1')}\r\n".encode(
                "latin-1"
            )
        )
        await writer.drain()

"""Faz stream do arquivo do CDN para o navegador"""
import ipaddress
import mimetypes
import re
import socket
from collections.abc import Iterator
from urllib.parse import quote, urljoin, urlparse

import httpx

CHUNK_SIZE = 64 * 1024
MAX_REDIRECTS = 3
TIMEOUT = httpx.Timeout(15.0, read=30.0)


class BlockedURL(Exception):
    pass


class UpstreamError(Exception):
    pass


def assert_public_url(url: str) -> None:
    """Evita SSRF: só http(s) para hosts que resolvem para IPs públicos."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise BlockedURL("URL inválida")
    try:
        addresses = {info[4][0] for info in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as exc:
        raise UpstreamError("não foi possível resolver o host") from exc
    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise BlockedURL("host não permitido")


def safe_filename(title: str | None, video_id: str | None, ext: str | None) -> str:
    base = re.sub(r"[^\w\- ]+", "", title or "", flags=re.UNICODE).strip()[:80]
    parts = [p for p in (base, str(video_id or "").strip()) if p]
    name = "-".join(parts) or "video"
    return f"{name}.{re.sub(r'[^a-z0-9]', '', (ext or 'mp4').lower()) or 'mp4'}"


def content_disposition(filename: str) -> str:
    ascii_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"


def media_type(filename: str, upstream: str | None) -> str:
    """CDNs às vezes mandam application/octet-stream; com o tipo de vídeo, o celular trata o arquivo como mídia."""
    guessed = mimetypes.guess_type(filename)[0]
    if guessed and guessed.startswith("video/"):
        return guessed
    return upstream or "application/octet-stream"


def open_stream(url: str, headers: dict | None = None) -> tuple[httpx.Client, httpx.Response]:
    """Abre o CDN seguindo redirects manualmente (revalidando cada destino)."""
    request_headers = {**(headers or {}), "Accept-Encoding": "identity"}
    client = httpx.Client(timeout=TIMEOUT, follow_redirects=False)
    try:
        for _ in range(MAX_REDIRECTS + 1):
            assert_public_url(url)
            resp = client.send(client.build_request("GET", url, headers=request_headers), stream=True)
            if resp.is_redirect and resp.headers.get("location"):
                url = urljoin(url, resp.headers["location"])
                resp.close()
                continue
            if resp.status_code >= 400:
                status = resp.status_code
                resp.close()
                raise UpstreamError(f"o servidor de origem respondeu {status}")
            return client, resp
        raise UpstreamError("redirecionamentos demais")
    except Exception:
        client.close()
        raise


def iterate(client: httpx.Client, resp: httpx.Response) -> Iterator[bytes]:
    try:
        yield from resp.iter_raw(CHUNK_SIZE)
    finally:
        resp.close()
        client.close()

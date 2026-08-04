from dataclasses import dataclass
import json
import shlex
from urllib.parse import urlparse

import httpx

from app.models.api_connector import APIConnector


MAX_RESPONSE_CHARS = 20_000


@dataclass(frozen=True)
class ParsedCurl:
    method: str
    url: str
    headers: dict[str, str]
    body: str | None = None


class APIConnectorError(ValueError):
    pass


def parse_curl_command(command: str) -> ParsedCurl:
    parts = shlex.split(command)
    if not parts or parts[0] != "curl":
        raise APIConnectorError("Paste a cURL command that starts with curl")

    method = "GET"
    headers: dict[str, str] = {}
    body_parts: list[str] = []
    url = ""
    i = 1

    while i < len(parts):
        token = parts[i]
        if token in ("-X", "--request") and i + 1 < len(parts):
            method = parts[i + 1].upper()
            i += 2
            continue
        if token.startswith("-X") and len(token) > 2:
            method = token[2:].upper()
            i += 1
            continue
        if token in ("-H", "--header") and i + 1 < len(parts):
            _add_header(headers, parts[i + 1])
            i += 2
            continue
        if token in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii") and i + 1 < len(parts):
            body_parts.append(parts[i + 1])
            i += 2
            continue
        if token.startswith("http://") or token.startswith("https://"):
            url = token
        i += 1

    if body_parts and method == "GET":
        method = "POST"
    _validate_method_and_url(method, url)
    return ParsedCurl(method=method, url=url, headers=headers, body="&".join(body_parts) if body_parts else None)


def apply_curl_to_payload(payload) -> None:
    if not getattr(payload, "curl_command", None):
        return
    parsed = parse_curl_command(payload.curl_command)
    payload.method = parsed.method
    payload.url = parsed.url
    payload.headers = parsed.headers
    payload.body = parsed.body


def validate_connector_config(method: str, url: str) -> None:
    _validate_method_and_url(method, url)


async def fetch_api_connector(connector: APIConnector) -> tuple[int, str]:
    _validate_method_and_url(connector.method, connector.url)
    headers = {str(k): str(v) for k, v in (connector.headers or {}).items()}
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.request(
            connector.method.upper(),
            connector.url,
            headers=headers,
            content=connector.body if connector.method.upper() == "POST" else None,
        )
    return response.status_code, _response_text(response)


def _add_header(headers: dict[str, str], header: str) -> None:
    name, sep, value = header.partition(":")
    if sep and name.strip():
        headers[name.strip()] = value.strip()


def _validate_method_and_url(method: str, url: str) -> None:
    if method.upper() not in {"GET", "POST"}:
        raise APIConnectorError("Only GET and POST API connectors are supported")
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise APIConnectorError("Connector URL must be http or https")


def _response_text(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type.lower():
        try:
            text = json.dumps(response.json(), indent=2, ensure_ascii=False)
        except ValueError:
            text = response.text
    else:
        text = response.text
    return text[:MAX_RESPONSE_CHARS]

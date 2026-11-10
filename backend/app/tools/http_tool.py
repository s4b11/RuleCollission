import ipaddress
import socket
from urllib.parse import urlparse

import httpx

from ..models import ToolDefinition

MAX_RESULT = 4000


def check_url(url: str) -> None:
    parts = urlparse(url)
    if parts.scheme != "https" or not parts.hostname:
        raise ValueError("External tools must use an https address")
    for info in socket.getaddrinfo(parts.hostname, None):
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise ValueError("External tools cannot point at private or local addresses")


def call(tool: ToolDefinition, arguments: dict) -> dict:
    check_url(tool.url)
    if tool.method == "GET":
        response = httpx.get(tool.url, params=arguments, headers=tool.headers, timeout=10)
    else:
        response = httpx.request(tool.method, tool.url, json=arguments, headers=tool.headers, timeout=10)
    return {"status": response.status_code, "untrusted_result": response.text[:MAX_RESULT]}

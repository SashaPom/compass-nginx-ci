import json
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlsplit

import pytest


@pytest.fixture(scope="session")
def request_page(target):
    address = urlsplit(target.base_url)
    connect = HTTPSConnection if address.scheme == "https" else HTTPConnection

    def get(route):
        client = connect(address.hostname, address.port, timeout=target.timeout)
        try:
            client.request("GET", address.path.rstrip("/") + route)
            response = client.getresponse()
            return response.status, response.headers.get_content_type(), response.read()
        finally:
            client.close()

    return get


@pytest.mark.parametrize(
    ("route", "expected"),
    (("/", 200), ("/health.json", 200), ("/missing-page", 404)),
    ids=("homepage", "health", "absent"),
)
def test_status_code(request_page, route, expected):
    status, _, _ = request_page(route)
    assert status == expected, f"{route}: expected {expected}, got {status}"


def test_homepage_release(request_page, target):
    status, _, body = request_page("/")
    assert status == 200
    assert target.release in body.decode("utf-8")


def test_json_health_values(request_page, target):
    status, _, body = request_page("/health.json")
    assert status == 200
    assert json.loads(body) == {"status": "ready", "release": target.release}


def test_health_media_type(request_page):
    status, media_type, _ = request_page("/health.json")
    assert status == 200
    assert media_type == "application/json"

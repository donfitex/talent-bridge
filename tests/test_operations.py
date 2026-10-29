from unittest.mock import patch

import pytest

pytestmark = pytest.mark.django_db


def test_health_and_openapi(client):
    assert client.get("/health/live/").status_code == 200
    assert client.get("/health/").status_code == 200
    with patch("apps.common.health.connection.cursor", side_effect=RuntimeError("unavailable")):
        response = client.get("/health/")
        assert response.status_code == 503
        assert b"unavailable" in response.content
    assert client.get("/api/schema/").status_code == 200
    assert client.get("/api/docs/").status_code == 200

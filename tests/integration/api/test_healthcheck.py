from __future__ import annotations


def test_healthcheck_returns_ok(integration_api_client) -> None:
    response = integration_api_client.get("/healthcheck")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


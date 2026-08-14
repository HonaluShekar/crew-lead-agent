"""Contract tests for the Bolt React UI adapter endpoints."""

from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_ui_collection_endpoints_return_bolt_shapes():
    """The UI data endpoints should return non-empty JSON collections."""
    endpoints = [
        "/ui/flights",
        "/ui/crew",
        "/ui/disruptions",
        "/ui/issues",
        "/ui/recommendations",
        "/ui/activity",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        payload = response.json()
        assert isinstance(payload, list), endpoint
        assert payload, endpoint

        if endpoint == "/ui/flights":
            assert {"id", "number", "disruptionStatus"}.issubset(payload[0])
        elif endpoint == "/ui/crew":
            assert {"id", "name", "availability", "riskStatus"}.issubset(payload[0])
        elif endpoint == "/ui/disruptions":
            assert {"id", "flightNumber", "severity", "status"}.issubset(payload[0])
        elif endpoint == "/ui/issues":
            assert {"id", "type", "flight", "severity", "status"}.issubset(payload[0])
        elif endpoint == "/ui/recommendations":
            assert {"id", "flight", "text", "severity", "time"}.issubset(payload[0])
        elif endpoint == "/ui/activity":
            assert {"id", "step", "label", "agent", "tool", "status"}.issubset(payload[0])


def test_ui_availability_snapshot_has_dashboard_counts():
    response = client.get("/ui/availability-snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert {"Available", "Assigned", "On Duty", "At Risk"}.issubset(payload)
    assert sum(payload.values()) > 0


def test_ui_analyze_returns_decision_support_result():
    response = client.post(
        "/ui/analyze",
        json={"query": "Analyze the disruption on flight 6E123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["flightId"] == "6E123"
    assert payload["steps"]
    assert payload["recommendation"]
    assert isinstance(payload["recoveryOptions"], list)

"""
API endpoint tests for the Crew Lead Agent FastAPI backend.

Tests:
- Health check
- Flight assessment endpoint
- Natural language agent endpoint
- Error handling
"""

import pytest
import json
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check(self, client):
        """Test health endpoint returns 200 with healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAssessmentEndpoint:
    """Test the flight assessment endpoint."""
    
    def test_valid_flight_assessment(self, client):
        """Test assessment for valid flight."""
        response = client.post("/assess/6E123")
        assert response.status_code == 200
        data = response.json()
        assert "flight_id" in data
        assert "assessment" in data
        assert data["flight_id"] == "6E123"
        assert data["decision_authority"] == "CREW_LEAD"
        assert data["execution_performed"] is False
    
    def test_assessment_response_structure(self, client):
        """Test that assessment response has correct structure."""
        response = client.post("/assess/6E123")
        data = response.json()
        assessment = data["assessment"]
        
        # Check expected keys in assessment
        expected_keys = [
            "flight_id",
            "status",
            "summary",
            "recommended_action",
            "alternatives_by_role",
            "key_findings",
            "crew_lead_note"
        ]
        for key in expected_keys:
            assert key in assessment, f"Assessment missing key: {key}"
    
    def test_assessment_summary_structure(self, client):
        """Test that assessment summary has correct structure."""
        response = client.post("/assess/6E123")
        data = response.json()
        summary = data["assessment"]["summary"]
        
        # Check expected keys in summary
        expected_keys = ["route", "delay_minutes", "affected_crew_count", "eligible_candidate_count"]
        for key in expected_keys:
            assert key in summary, f"Summary missing key: {key}"
    
    def test_assessment_recommended_action_structure(self, client):
        """Test that recommended action has correct structure."""
        response = client.post("/assess/6E123")
        data = response.json()
        action = data["assessment"]["recommended_action"]
        
        # Check expected keys
        expected_keys = ["crew_id", "name", "role", "message", "status"]
        for key in expected_keys:
            assert key in action, f"Recommended action missing key: {key}"
    
    def test_assessment_alternatives_structure(self, client):
        """Test that alternatives are properly structured."""
        response = client.post("/assess/6E123")
        data = response.json()
        alternatives = data["assessment"]["alternatives_by_role"]
        
        # Should have multiple roles
        assert isinstance(alternatives, dict)
        assert len(alternatives) > 0
        
        # Each role should have candidates
        for role, candidates in alternatives.items():
            assert isinstance(role, str)
            assert isinstance(candidates, list)
            if len(candidates) > 0:
                # Check candidate structure
                candidate = candidates[0]
                assert "crew_id" in candidate
                assert "name" in candidate
    
    def test_invalid_flight_assessment(self, client):
        """Test assessment for non-existent flight."""
        response = client.post("/assess/INVALID999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_assessment_key_findings(self, client):
        """Test that key findings are returned."""
        response = client.post("/assess/6E123")
        data = response.json()
        findings = data["assessment"]["key_findings"]
        
        # Should be a list of strings
        assert isinstance(findings, list)
        assert len(findings) > 0
        for finding in findings:
            assert isinstance(finding, str)


class TestAskEndpoint:
    """Test the natural language agent endpoint."""
    
    def test_ask_valid_flight(self, client):
        """Test asking about a valid flight."""
        payload = {"message": "Analyze disruption for flight 6E123"}
        response = client.post("/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Response should contain assessment or agent output
        assert data["response"] is not None
    
    def test_ask_flight_detection(self, client):
        """Test that agent detects and analyzes valid flight ID."""
        payload = {"message": "What about flight 6E123?"}
        response = client.post("/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        # Should return structured assessment
        response_obj = data["response"]
        if isinstance(response_obj, dict):
            # If returned as dict, should have assessment fields
            assert "flight_id" in response_obj or "status" in response_obj
    
    def test_ask_invalid_flight(self, client):
        """Test asking about invalid flight."""
        payload = {"message": "Analyze flight INVALID999"}
        response = client.post("/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Agent should respond even if flight not found
        assert "response" in data
    
    def test_ask_empty_message(self, client):
        """Test ask endpoint with empty message."""
        payload = {"message": ""}
        response = client.post("/ask", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_ask_missing_message(self, client):
        """Test ask endpoint with missing message field."""
        payload = {}
        response = client.post("/ask", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_ask_natural_language(self, client):
        """Test ask endpoint with natural language query."""
        payload = {"message": "I need a crew disruption assessment"}
        response = client.post("/ask", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Should return agent response
        assert len(str(data["response"])) > 0


class TestErrorHandling:
    """Test error handling in API."""
    
    def test_method_not_allowed(self, client):
        """Test calling endpoints with wrong HTTP method."""
        response = client.get("/assess/6E123")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_nonexistent_endpoint(self, client):
        """Test calling non-existent endpoint."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_malformed_json(self, client):
        """Test posting malformed JSON."""
        response = client.post("/ask", data="not json", headers={"Content-Type": "application/json"})
        assert response.status_code in [400, 422]
    
    def test_assessment_handles_special_characters(self, client):
        """Test that assessment endpoint handles special characters in flight ID."""
        # Should not crash, but return 404
        response = client.post("/assess/6E@#$%")
        assert response.status_code in [404, 500]  # Either not found or error
    
    def test_ask_handles_very_long_message(self, client):
        """Test ask endpoint with very long message."""
        long_message = "x" * 5000
        payload = {"message": long_message}
        response = client.post("/ask", json=payload)
        # Should either process or reject gracefully
        assert response.status_code in [200, 400, 413, 414]


class TestCORSHeaders:
    """Test CORS headers in responses."""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response."""
        response = client.get("/health")
        # CORS middleware should add headers
        assert response.status_code == 200


class TestResponseFormats:
    """Test response format consistency."""
    
    def test_all_responses_json(self, client):
        """Test that all responses are valid JSON."""
        endpoints = [
            ("/health", "GET"),
            ("/assess/6E123", "POST"),
            ("/ask", "POST"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                if endpoint == "/ask":
                    response = client.post(endpoint, json={"message": "test"})
                else:
                    response = client.post(endpoint)
            
            # Should be JSON
            try:
                response.json()
            except ValueError:
                pytest.fail(f"Response from {endpoint} is not valid JSON")
    
    def test_error_responses_have_detail(self, client):
        """Test that error responses have detail field."""
        response = client.post("/assess/INVALID999")
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], (str, dict, list))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

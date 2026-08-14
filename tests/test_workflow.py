"""
Unit tests for the crew disruption assessment workflow.

Tests the rule engine, candidate evaluation, and assessment functions.
"""

import pytest
from datetime import datetime, timedelta
from src.crew_lead.workflow import (
    evaluate_candidate_for_replacement,
    find_eligible_replacements,
    build_crew_lead_report,
    _is_crew_available,
    _is_qualified,
    _is_duty_legal,
    _is_location_compatible,
    _has_schedule_conflict,
)
from src.crew_lead.tools.data_loader import load_crew, load_flights, load_assignments


class TestCrewAvailability:
    """Test crew availability checks."""
    
    def test_available_crew(self):
        """Test that AVAILABLE crew passes availability check."""
        crew = {
            "crew_id": "C1842",
            "name": "Rohan Mehta",
            "status": "AVAILABLE",
            "available_from": None
        }
        result = _is_crew_available(crew, datetime.now())
        assert result["eligible"] is True
        assert "AVAILABLE" in result["reason"]
    
    def test_unavailable_crew(self):
        """Test that non-AVAILABLE crew fails check."""
        crew = {
            "crew_id": "C1843",
            "name": "Test Crew",
            "status": "REST",
            "available_from": None
        }
        result = _is_crew_available(crew, datetime.now())
        assert result["eligible"] is False
        assert "not available" in result["reason"].lower()
    
    def test_crew_available_from_future(self):
        """Test crew that becomes available in future."""
        now = datetime.now()
        future_time = (now + timedelta(hours=2)).strftime("%H:%M")
        crew = {
            "crew_id": "C1844",
            "name": "Test Crew",
            "status": "AVAILABLE",
            "available_from": future_time
        }
        result = _is_crew_available(crew, now)
        assert result["eligible"] is False
        assert "available only from" in result["reason"].lower()


class TestQualifications:
    """Test crew qualification checks."""
    
    def test_qualified_crew(self):
        """Test crew with matching qualification."""
        crew = {
            "crew_id": "C1842",
            "name": "Rohan Mehta",
            "qualification": "A320"
        }
        flight = {
            "flight_id": "6E123",
            "aircraft": "A320"
        }
        result = _is_qualified(crew, flight)
        assert result["eligible"] is True
        assert "A320" in result["reason"]
    
    def test_unqualified_crew(self):
        """Test crew without matching qualification."""
        crew = {
            "crew_id": "C1843",
            "name": "Test Crew",
            "qualification": "B787"
        }
        flight = {
            "flight_id": "6E123",
            "aircraft": "A320"
        }
        result = _is_qualified(crew, flight)
        assert result["eligible"] is False
        assert "does not include" in result["reason"]
    
    def test_missing_qualification(self):
        """Test crew with missing qualification."""
        crew = {
            "crew_id": "C1844",
            "name": "Test Crew",
            "qualification": None
        }
        flight = {
            "flight_id": "6E123",
            "aircraft": "A320"
        }
        result = _is_qualified(crew, flight)
        assert result["eligible"] is False
        assert "missing" in result["reason"].lower()


class TestDutyLegal:
    """Test duty-time legality checks."""
    
    def test_crew_within_duty_limit(self):
        """Test crew with remaining duty time."""
        now = datetime.now()
        # 2 hours ago
        duty_start = (now - timedelta(hours=2)).strftime("%H:%M")
        crew = {
            "crew_id": "C1842",
            "name": "Rohan Mehta",
            "duty_start": duty_start
        }
        result = _is_duty_legal(crew, now)
        assert result["eligible"] is True
        assert result["status"] == "OK"
        assert "hours remain" in result["reason"].lower()
    
    def test_crew_duty_limit_reached(self):
        """Test crew that reached duty limit."""
        now = datetime.now()
        # 8.5 hours ago (exceeds 8-hour limit)
        duty_start = (now - timedelta(hours=8, minutes=30)).strftime("%H:%M")
        crew = {
            "crew_id": "C1843",
            "name": "Test Crew",
            "duty_start": duty_start
        }
        result = _is_duty_legal(crew, now)
        assert result["eligible"] is False
        assert result["status"] == "LIMIT_REACHED"
    
    def test_crew_duty_high_risk(self):
        """Test crew with less than 1 hour remaining."""
        now = datetime.now()
        # 7.5 hours ago (only 30 min remaining)
        duty_start = (now - timedelta(hours=7, minutes=30)).strftime("%H:%M")
        crew = {
            "crew_id": "C1844",
            "name": "Test Crew",
            "duty_start": duty_start
        }
        result = _is_duty_legal(crew, now)
        assert result["eligible"] is False
        assert result["status"] == "HIGH_RISK"
        assert "only" in result["reason"].lower() and "hours remain" in result["reason"].lower()


class TestLocationCompatibility:
    """Test location/positioning checks."""
    
    def test_crew_at_base(self):
        """Test crew at same base as flight origin."""
        crew = {
            "crew_id": "C1842",
            "name": "Rohan Mehta",
            "base": "DEL"
        }
        flight = {
            "flight_id": "6E123",
            "origin": "DEL"
        }
        result = _is_location_compatible(crew, flight)
        assert result["eligible"] is True
        assert result["status"] == "READY_AT_BASE"
    
    def test_crew_different_base(self):
        """Test crew at different base (requires positioning)."""
        crew = {
            "crew_id": "C6290",
            "name": "Rahul Verma",
            "base": "BOM"
        }
        flight = {
            "flight_id": "6E123",
            "origin": "DEL"
        }
        result = _is_location_compatible(crew, flight)
        assert result["eligible"] is True
        assert result["status"] == "POSITIONING_REQUIRED"
        assert "positioning" in result["reason"].lower()


class TestScheduleConflicts:
    """Test assignment conflict checks."""
    
    def test_no_conflict(self):
        """Test crew with no conflicting assignments."""
        # Crew C1842 should not have conflicts for flight 6E123
        result = _has_schedule_conflict("C1842", "6E123")
        assert result["eligible"] is True
        assert result["status"] == "NO_CONFLICT"
    
    def test_invalid_flight(self):
        """Test conflict check for non-existent flight."""
        result = _has_schedule_conflict("C1842", "INVALID999")
        assert result["eligible"] is True
        assert "not found" in result["reason"].lower()


class TestCandidateEvaluation:
    """Test complete candidate evaluation."""
    
    def test_evaluate_good_candidate(self):
        """Test evaluation of a good replacement candidate."""
        result = evaluate_candidate_for_replacement("C1842", "6E123", "CAPTAIN")
        assert result["status"] == "ELIGIBLE"
        assert result["crew_id"] == "C1842"
        assert result["name"] == "Rohan Mehta"
        assert result["role"] == "CAPTAIN"
    
    def test_evaluate_wrong_role(self):
        """Test evaluation of crew with wrong role."""
        # C1842 is Captain, try to use for First Officer
        result = evaluate_candidate_for_replacement("C1842", "6E123", "FIRST_OFFICER")
        assert result["status"] == "REJECTED"
        assert "role" in result["reason"].lower()
    
    def test_evaluate_invalid_crew(self):
        """Test evaluation of non-existent crew."""
        result = evaluate_candidate_for_replacement("INVALID999", "6E123", "CAPTAIN")
        assert result["status"] == "REJECTED"
        assert "not found" in result["reason"].lower()


class TestFindEligibleReplacements:
    """Test finding eligible replacement crew."""
    
    def test_find_captains(self):
        """Test finding eligible Captains."""
        replacements = find_eligible_replacements("6E123", "CAPTAIN")
        assert isinstance(replacements, list)
        assert len(replacements) > 0
        # All results should be Captains
        for crew in replacements:
            assert crew["role"].upper() == "CAPTAIN"
            assert crew["status"] == "ELIGIBLE"
    
    def test_find_invalid_flight(self):
        """Test finding replacements for invalid flight."""
        replacements = find_eligible_replacements("INVALID999", "CAPTAIN")
        assert replacements == []
    
    def test_find_invalid_role(self):
        """Test finding replacements for invalid role."""
        replacements = find_eligible_replacements("6E123", "INVALID_ROLE")
        assert replacements == []


class TestBuildReport:
    """Test complete assessment report building."""
    
    def test_valid_flight_report(self):
        """Test building report for valid flight."""
        report = build_crew_lead_report("6E123")
        assert report is not None
        assert report.get("status") is not None
        assert report.get("flight_id") == "6E123" or "status" in report
    
    def test_invalid_flight_report(self):
        """Test building report for invalid flight."""
        report = build_crew_lead_report("INVALID999")
        assert report.get("status") == "NOT_FOUND" or report.get("error") is not None
    
    def test_report_contains_key_info(self):
        """Test that report contains expected structure."""
        report = build_crew_lead_report("6E123")
        if report.get("status") != "NOT_FOUND":
            # Valid report should have these keys
            expected_keys = ["flight_id", "status", "summary", "recommended_action"]
            for key in expected_keys:
                assert key in report, f"Report missing key: {key}"


# ============================================================
# INTEGRATION TESTS
# ============================================================

class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_assessment_workflow(self):
        """Test complete assessment workflow."""
        # 1. Get flight
        flights = load_flights()
        flight = next((f for f in flights if f["flight_id"] == "6E123"), None)
        assert flight is not None
        
        # 2. Find replacements
        replacements = find_eligible_replacements("6E123", "CAPTAIN")
        assert len(replacements) > 0
        
        # 3. Evaluate best candidate
        best = replacements[0]
        evaluation = evaluate_candidate_for_replacement(
            best["crew_id"], "6E123", "CAPTAIN"
        )
        assert evaluation["status"] == "ELIGIBLE"
    
    def test_multiple_flights(self):
        """Test assessment for multiple flights."""
        flights = load_flights()
        for flight in flights[:3]:
            flight_id = flight["flight_id"]
            report = build_crew_lead_report(flight_id)
            assert report is not None
            # All flights should have some status
            assert report.get("status") is not None or report.get("error") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

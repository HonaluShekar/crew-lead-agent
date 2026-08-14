from datetime import datetime

from src.crew_lead.workflow import (
    analyze_disruption,
    build_crew_lead_report,
    find_eligible_replacements,
    generate_recovery_options,
)


def test_find_eligible_replacements_for_flight_6E123():
    options = find_eligible_replacements("6E123", "Captain")

    assert isinstance(options, list)
    assert len(options) >= 1
    assert any(candidate["crew_id"] in {"C1842", "C6290"} for candidate in options)


def test_generate_recovery_options_for_flight_6E123():
    options = generate_recovery_options(
        "6E123",
        reference_time=datetime(2026, 8, 13, 12, 0),
    )

    assert options["status"] in {"RECOVERY_OPTIONS_AVAILABLE", "RECOVERY_GAPS_PRESENT"}
    assert "recommended_candidate" in options
    assert "role_breakdown" in options
    assert "summary" in options


def test_analyze_disruption_returns_structured_result():
    result = analyze_disruption(
        "6E123",
        reference_time=datetime(2026, 8, 13, 12, 0),
    )

    assert result["flight_id"] == "6E123"
    assert "affected_crew" in result
    assert "eligible_replacements" in result
    assert "downstream_impact" in result
    assert "recommended_action" in result


def test_build_crew_lead_report_returns_readable_summary():
    report = build_crew_lead_report(
        "6E123",
        reference_time=datetime(2026, 8, 13, 12, 0),
    )

    assert report["flight_id"] == "6E123"
    assert "summary" in report
    assert "recommended_action" in report
    assert "key_findings" in report
    assert isinstance(report["key_findings"], list)

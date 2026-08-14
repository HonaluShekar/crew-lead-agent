"""Adapters that expose the Python prototype data in the UI's shape.

The operational rules remain in :mod:`crew_lead.workflow` and the tool
modules.  This module only translates those results into the camelCase
objects consumed by the React operations console.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .tools.assessment_tools import complete_disruption_assessment
from .tools.data_loader import load_assignments, load_crew, load_flights
from .tools.duty_tools import check_duty_risk
from .tools.impact_tools import get_downstream_flights
from .workflow import build_crew_lead_report


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _hours_to_minutes(value: Any) -> int:
    try:
        return round(float(value) * 60)
    except (TypeError, ValueError):
        return 0


def _time_as_iso(value: Optional[str], reference: Optional[datetime] = None) -> Optional[str]:
    """Convert the CSV HH:MM values into timestamps the browser can format."""

    if not value:
        return None

    try:
        parsed = datetime.strptime(str(value), "%H:%M")
    except ValueError:
        return None

    base = reference or datetime.now()
    return base.replace(
        hour=parsed.hour,
        minute=parsed.minute,
        second=0,
        microsecond=0,
    ).isoformat(timespec="seconds")


def _risk_status(risk: Optional[str]) -> str:
    return {
        "LOW": "Safe",
        "MEDIUM": "Watch",
        "HIGH": "At Risk",
        "LIMIT_REACHED": "Critical",
    }.get((risk or "").upper(), "Safe")


def _availability_status(status: Optional[str]) -> str:
    return {
        "AVAILABLE": "Available",
        "ON_DUTY": "On Duty",
        "ASSIGNED": "Assigned",
        "RESTING": "Resting",
        "REST": "Resting",
    }.get((status or "").upper(), "Unavailable")


def _rest_status(risk: Optional[str]) -> str:
    normalized = (risk or "").upper()
    if not normalized:
        return "Rest Required"
    if normalized == "LIMIT_REACHED":
        return "Insufficient"
    if normalized in {"HIGH", "MEDIUM"}:
        return "Rest Required"
    return "Rested"


def _flight_map() -> Dict[str, Dict[str, Any]]:
    return {flight["flight_id"]: flight for flight in load_flights()}


def _assignment_map() -> Dict[str, List[Dict[str, Any]]]:
    assignments_by_crew: Dict[str, List[Dict[str, Any]]] = {}
    for assignment in load_assignments():
        assignments_by_crew.setdefault(assignment["crew_id"], []).append(assignment)
    return assignments_by_crew


def _crew_risk(crew: Dict[str, Any]) -> Dict[str, Any]:
    return check_duty_risk(crew["crew_id"])


def _schedule_conflicts(
    crew_id: str,
    assignments: List[Dict[str, Any]],
    flights: Dict[str, Dict[str, Any]],
) -> List[str]:
    departures: List[tuple[str, datetime]] = []
    for assignment in assignments:
        flight = flights.get(assignment.get("flight_id"))
        if not flight:
            continue
        value = flight.get("estimated_departure") or flight.get("scheduled_departure")
        try:
            departure = datetime.strptime(value, "%H:%M")
        except (TypeError, ValueError):
            continue
        departures.append((assignment["flight_id"], departure))

    conflicts: List[str] = []
    for index, (flight_id, departure) in enumerate(departures):
        for other_flight_id, other_departure in departures[index + 1 :]:
            if abs((departure - other_departure).total_seconds()) < 1800:
                conflicts.append(
                    f"Schedule overlap between {flight_id} and {other_flight_id}."
                )
    return conflicts


def build_ui_crew() -> List[Dict[str, Any]]:
    """Return crew records in the shape expected by the React UI."""

    reference = datetime.now()
    flights = _flight_map()
    assignments_by_crew = _assignment_map()
    result: List[Dict[str, Any]] = []

    for member in load_crew():
        crew_id = member["crew_id"]
        assignments = assignments_by_crew.get(crew_id, [])
        assignments.sort(
            key=lambda item: (
                flights.get(item.get("flight_id"), {}).get("estimated_departure")
                or "99:99"
            )
        )

        duty = _crew_risk(member)
        risk = duty.get("risk")
        current_assignment = assignments[0] if assignments else None
        current_flight = current_assignment.get("flight_id") if current_assignment else None

        upcoming = []
        for assignment in assignments[1:]:
            flight = flights.get(assignment.get("flight_id"))
            if not flight:
                continue
            upcoming.append(
                {
                    "flightNumber": flight["flight_id"],
                    "departure": _time_as_iso(
                        flight.get("estimated_departure")
                        or flight.get("scheduled_departure"),
                        reference,
                    ),
                    "route": f"{flight.get('origin')} → {flight.get('destination')}",
                }
            )

        conflicts = _schedule_conflicts(crew_id, assignments, flights)
        if risk in {"HIGH", "LIMIT_REACHED"}:
            conflicts.insert(
                0,
                "Duty-time risk requires review before another assignment.",
            )

        result.append(
            {
                "id": crew_id,
                "name": member.get("name"),
                "role": member.get("role"),
                "base": member.get("base"),
                "qualification": member.get("qualification"),
                "currentFlight": current_flight,
                "dutyStart": _time_as_iso(member.get("duty_start"), reference),
                "dutyElapsedMinutes": _hours_to_minutes(duty.get("elapsed_hours")),
                "dutyRemainingMinutes": _hours_to_minutes(duty.get("remaining_hours")),
                "restStatus": _rest_status(risk),
                "availability": _availability_status(member.get("status")),
                "riskStatus": _risk_status(risk),
                "upcoming": upcoming,
                "conflicts": conflicts,
            }
        )

    return result


def _flight_legality(
    flight: Dict[str, Any],
    crew_map: Dict[str, Dict[str, Any]],
    assignments: List[Dict[str, Any]],
) -> str:
    statuses: List[str] = []
    for assignment in assignments:
        member = crew_map.get(assignment.get("crew_id"))
        if not member:
            statuses.append("Illegal")
            continue

        duty = _crew_risk(member)
        if duty.get("risk") == "LIMIT_REACHED":
            statuses.append("Illegal")
        elif duty.get("risk") in {"HIGH", "MEDIUM"}:
            statuses.append("At Risk")

        qualification = str(member.get("qualification") or "")
        if flight.get("aircraft") not in qualification:
            statuses.append("Illegal")

    if "Illegal" in statuses:
        return "Illegal"
    if "At Risk" in statuses:
        return "At Risk"
    return "Legal"


def build_ui_flights() -> List[Dict[str, Any]]:
    """Return flights with assigned crew and downstream impact attached."""

    reference = datetime.now()
    flights = _flight_map()
    crew_map = {member["crew_id"]: member for member in load_crew()}
    assignments = load_assignments()
    result: List[Dict[str, Any]] = []

    for flight in flights.values():
        flight_id = flight["flight_id"]
        flight_assignments = [
            assignment for assignment in assignments if assignment["flight_id"] == flight_id
        ]
        assigned_crew = [assignment["crew_id"] for assignment in flight_assignments]
        downstream = get_downstream_flights(flight_id)
        crew_status = _flight_legality(flight, crew_map, flight_assignments)
        delay_minutes = _as_int(flight.get("delay_minutes"))
        disruption_status = "Crew Issue" if crew_status != "Legal" else (
            "Delay" if delay_minutes > 0 else "None"
        )

        result.append(
            {
                "id": flight_id,
                "number": flight_id,
                "origin": flight.get("origin"),
                "destination": flight.get("destination"),
                "aircraft": flight.get("aircraft"),
                "scheduledDeparture": _time_as_iso(
                    flight.get("scheduled_departure"), reference
                ),
                "estimatedDeparture": _time_as_iso(
                    flight.get("estimated_departure"), reference
                ),
                "arrival": _time_as_iso(flight.get("scheduled_arrival"), reference),
                "delayMinutes": delay_minutes,
                "assignedCrew": assigned_crew,
                "crewStatus": crew_status,
                "disruptionStatus": disruption_status,
                "downstreamImpact": len(downstream),
                "downstreamFlights": [item["flight_id"] for item in downstream],
                "route": f"{flight.get('origin')} → {flight.get('destination')}",
            }
        )

    return result


def build_ui_disruptions() -> List[Dict[str, Any]]:
    flights = build_ui_flights()
    disruptions: List[Dict[str, Any]] = []

    for flight in flights:
        if flight["disruptionStatus"] == "None":
            continue

        if flight["crewStatus"] == "Illegal" or flight["delayMinutes"] >= 120:
            severity = "Critical"
        elif flight["delayMinutes"] >= 60 or flight["crewStatus"] == "At Risk":
            severity = "High"
        else:
            severity = "Medium"

        if flight["crewStatus"] != "Legal":
            disruption_type = "Crew Legality"
            reason = "Assigned crew requires duty-time or qualification review."
        else:
            disruption_type = "Delay"
            reason = f"Flight is delayed by {flight['delayMinutes']} minutes."

        disruptions.append(
            {
                "id": f"D-{flight['number']}",
                "flightNumber": flight["number"],
                "origin": flight["origin"],
                "destination": flight["destination"],
                "scheduledDeparture": flight["scheduledDeparture"],
                "estimatedDeparture": flight["estimatedDeparture"],
                "delayMinutes": flight["delayMinutes"],
                "type": disruption_type,
                "assignedCrew": flight["assignedCrew"],
                "crewLegality": flight["crewStatus"],
                "downstreamFlights": flight["downstreamFlights"],
                "severity": severity,
                "status": "Active",
                "reason": reason,
            }
        )

    return disruptions


def build_ui_issues() -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    now = datetime.now().isoformat(timespec="seconds")

    for disruption in build_ui_disruptions():
        if disruption["type"] == "Crew Legality":
            issue_type = "Duty Time"
            action = "Review duty-time, qualification, and replacement options."
        elif disruption["downstreamFlights"]:
            issue_type = "Downstream Impact"
            action = "Assess downstream crew impact before accepting delay."
        else:
            issue_type = "Replacement Required"
            action = "Review available replacement crew."

        status = {
            "Critical": "Action Required",
            "High": "Investigating",
            "Medium": "New",
            "Low": "New",
        }[disruption["severity"]]

        issues.append(
            {
                "id": f"ISS-{disruption['flightNumber']}",
                "type": issue_type,
                "flight": disruption["flightNumber"],
                "severity": disruption["severity"],
                "crewAffected": len(disruption["assignedCrew"]),
                "crewIds": disruption["assignedCrew"],
                "createdTime": now,
                "status": status,
                "owner": "Crew Lead",
                "recommendedAction": action,
                "description": disruption["reason"],
            }
        )

    return issues


def build_ui_snapshot() -> Dict[str, int]:
    snapshot = {
        "Available": 0,
        "Assigned": 0,
        "On Duty": 0,
        "Resting": 0,
        "Unavailable": 0,
        "At Risk": 0,
    }
    for member in build_ui_crew():
        availability = member["availability"]
        risk = member["riskStatus"]
        if availability in snapshot:
            snapshot[availability] += 1
        if risk in {"At Risk", "Critical"}:
            snapshot["At Risk"] += 1
    return snapshot


def build_ui_recommendations() -> List[Dict[str, Any]]:
    recommendations: List[Dict[str, Any]] = []
    now = datetime.now().isoformat(timespec="seconds")
    for disruption in build_ui_disruptions():
        report = build_crew_lead_report(disruption["flightNumber"])
        action = report.get("recommended_action") or {}
        recommendations.append(
            {
                "id": f"R-{disruption['flightNumber']}",
                "flight": disruption["flightNumber"],
                "text": action.get("message") or "Review recovery options with the Crew Lead.",
                "severity": disruption["severity"],
                "time": now,
            }
        )
    return recommendations


def build_ui_activity(flight_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Build a current, non-persisted workflow snapshot for the activity page."""

    target = flight_id or next(
        (flight["flight_id"] for flight in load_flights() if _as_int(flight.get("delay_minutes")) > 0),
        load_flights()[0]["flight_id"],
    )
    assessment = complete_disruption_assessment(target)
    if "error" in assessment:
        return []

    now = datetime.now()
    assigned_count = len(assessment.get("assigned_crew", []))
    replacement_count = sum(
        item.get("candidates_found", 0)
        for item in assessment.get("replacement_options", [])
    )
    downstream_count = len(assessment.get("downstream_impact", []))
    definitions = [
        ("Query received", "Orchestrator", "query_ingest", "Assessment request prepared."),
        ("Flight loaded", "Deterministic Workflow", "flight_lookup", f"Loaded {target} operational data."),
        ("Crew evaluated", "Duty Rules", "crew_assessment", f"Evaluated {assigned_count} assigned crew members."),
        ("Replacement candidates evaluated", "Recovery Planner", "recovery_candidate_evaluation", f"Found {replacement_count} candidate options."),
        ("Downstream impact checked", "Impact Analysis", "downstream_impact", f"Found {downstream_count} downstream flight entries."),
        ("Recommendation generated", "Recovery Planner", "recovery_recommendation", "Prepared decision-support output."),
    ]

    entries = []
    for index, (label, agent, tool, description) in enumerate(definitions, start=1):
        entries.append(
            {
                "id": f"activity-{target}-{index}",
                "step": index,
                "label": label,
                "agent": agent,
                "tool": tool,
                "description": description,
                "timestamp": (now - timedelta(seconds=len(definitions) - index)).isoformat(timespec="seconds"),
                "status": "Completed",
                "durationMs": 40 + index * 25,
            }
        )
    return entries


def _extract_flight_id(query: str) -> Optional[str]:
    matches = re.findall(r"\b([A-Z]{2})\s*(\d{3,4})\b", query.upper())
    if not matches:
        return None
    prefix, number = matches[0]
    return f"{prefix}{number}"


def _analysis_steps() -> List[Dict[str, Any]]:
    definitions = [
        ("query", "Query Received", "Orchestrator", "User query received by the backend."),
        ("understand", "Query Understanding", "Orchestrator", "Identified the target flight and decision criteria."),
        ("plan", "Plan Generated", "Recovery Planning", "Created a deterministic assessment plan."),
        ("availability", "Crew Availability Check", "Crew Rules", "Checked crew status and availability."),
        ("duty", "Duty-Time Check", "Duty Rules", "Evaluated prototype duty-time risk."),
        ("qualification", "Qualification Check", "Crew Rules", "Checked aircraft qualification compatibility."),
        ("impact", "Downstream Flight Impact", "Impact Analysis", "Checked later flights involving assigned crew."),
        ("replacements", "Replacement Candidate Search", "Recovery Planning", "Ranked eligible replacement options."),
        ("options", "Recovery Options", "Recovery Planning", "Prepared options and tradeoffs."),
        ("recommendation", "Final Recommendation", "Recovery Planning", "Prepared decision-support output for Crew Lead review."),
    ]
    return [
        {
            "id": step_id,
            "label": label,
            "agent": agent,
            "description": description,
            "status": "Waiting",
        }
        for step_id, label, agent, description in definitions
    ]


def build_ui_analysis(query: str) -> Dict[str, Any]:
    """Run the existing deterministic assessment and adapt it for AI Crew Lead."""

    flight_id = _extract_flight_id(query)
    if flight_id is None:
        flight_id = next(
            (flight["flight_id"] for flight in load_flights() if _as_int(flight.get("delay_minutes")) > 0),
            None,
        )

    if not flight_id:
        raise ValueError("No flight ID was found and no delayed flight is available for assessment.")

    report = build_crew_lead_report(flight_id)
    if report.get("status") == "NOT_FOUND":
        raise ValueError(f"Flight {flight_id} was not found.")

    assessment = complete_disruption_assessment(flight_id)
    action = report.get("recommended_action") or {}
    recommendation_status = action.get("status") or "NO_CANDIDATE"
    risk = {
        "READY": "Low",
        "POSITIONING_REQUIRED": "Medium",
        "REVIEW_REQUIRED": "Medium",
    }.get(recommendation_status, "High")
    affected_crew = [item.get("crew_id") for item in assessment.get("assigned_crew", [])]
    downstream = assessment.get("downstream_impact", [])
    recommendation = {
        "id": f"recommendation-{flight_id}",
        "title": f"Recovery assessment for {flight_id}",
        "recommendedAction": action.get("message") or "No clean replacement was found; escalate for Crew Lead review.",
        "reason": report.get("key_findings", [])
        + [
            "This is decision-support information only; no operational change was executed.",
        ],
        "affectedFlight": f"{flight_id} · {report['summary']['route']}",
        "affectedCrew": affected_crew,
        "dutyTimeImpact": (
            f"{assessment.get('assessment_summary', {}).get('limit_reached_crew_count', 0)} crew members at the prototype duty limit; "
            f"{assessment.get('assessment_summary', {}).get('high_risk_crew_count', 0)} additional crew members at high risk."
        ),
        "downstreamImpactSummary": f"{len(downstream)} downstream flight entries require review.",
        "impact": {
            "downstreamProtected": len(downstream) if recommendation_status == "READY" else 0,
            "reassignments": 1 if action.get("crew_id") else 0,
        },
        "risk": risk,
        "crewId": action.get("crew_id"),
        "flightNumber": flight_id,
    }

    recovery_options: List[Dict[str, Any]] = []
    alternatives: List[Dict[str, Any]] = []
    # Use the same candidate set as the deterministic /assess path.  The
    # legacy agent tools intentionally use a broader conflict heuristic and
    # would otherwise contradict the recommendation shown above.
    for role, candidates in report.get("alternatives_by_role", {}).items():
        candidates = candidates or []
        if not candidates:
            alternatives.append(
                {
                    "id": f"alternative-{flight_id}-{role}",
                    "summary": f"No replacement candidate found for {role}.",
                    "tradeoffs": ["Escalation or standby sourcing is required."],
                    "risk": "High",
                }
            )
            continue

        for candidate in candidates:
            candidate_id = candidate.get("crew_id")
            candidate_status = candidate.get("recommendation_status", "REVIEW_REQUIRED")
            candidate_duty = check_duty_risk(candidate_id) if candidate_id else {}
            candidate_risk = {
                "READY": "Low",
                "POSITIONING_REQUIRED": "Medium",
            }.get(candidate_status, "High")
            is_recommended = candidate_id == action.get("crew_id")
            tradeoffs = []
            if candidate_status == "POSITIONING_REQUIRED":
                tradeoffs.append("Positioning feasibility must be verified.")
            if candidate.get("conflicts"):
                tradeoffs.append("Existing assignment conflict detected.")
            if not tradeoffs:
                tradeoffs.append("Final availability and airline-specific legality checks remain required.")

            recovery_options.append(
                {
                    "id": f"recovery-{flight_id}-{candidate_id}",
                    "action": f"Use {candidate_id} as {role} replacement on {flight_id}.",
                    "crewIds": [candidate_id],
                    "qualificationStatus": "Qualified",
                    "dutyRemainingMinutes": _hours_to_minutes(candidate_duty.get("remaining_hours")),
                    "restStatus": _rest_status(candidate_duty.get("risk")),
                    "downstreamImpact": {
                        "flightsProtected": len(downstream) if is_recommended else 0,
                        "flightsAtRisk": [] if is_recommended else [item.get("flight_id") for item in downstream],
                    },
                    "operationalRisk": candidate_risk,
                    "tradeoffs": tradeoffs,
                    "recommended": is_recommended,
                }
            )

            if not is_recommended:
                alternatives.append(
                    {
                        "id": f"alternative-{flight_id}-{candidate_id}",
                        "summary": f"Use {candidate_id} ({candidate.get('name')}) as {role}; status: {candidate_status}.",
                        "tradeoffs": tradeoffs,
                        "risk": candidate_risk,
                    }
                )

    return {
        "flightId": flight_id,
        "steps": _analysis_steps(),
        "recommendation": recommendation,
        "alternatives": alternatives,
        "recoveryOptions": recovery_options,
    }

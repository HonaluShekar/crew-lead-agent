from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .tools.assignment_tools import get_flight_crew
from .tools.data_loader import load_assignments, load_crew, load_flights
from .tools.flight_tools import get_flight
from .tools.impact_tools import get_downstream_flights


DEFAULT_MAX_DUTY_HOURS = 8.0


def _normalize_role(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).strip().upper().replace("_", " ")


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M")
    except ValueError:
        return None


def _reference_time(reference_time: Optional[datetime] = None) -> datetime:
    return reference_time or datetime.now()


def _is_crew_available(crew: Dict[str, Any], reference_time: datetime) -> Dict[str, Any]:
    status = (crew.get("status") or "").upper()
    available_from = crew.get("available_from") or crew.get("duty_start")

    if status != "AVAILABLE":
        return {
            "eligible": False,
            "reason": f"Crew is not available; current status is {status or 'UNKNOWN'}.",
        }

    if available_from:
        available_dt = _parse_time(available_from)
        if available_dt is not None:
            available_dt = reference_time.replace(
                hour=available_dt.hour,
                minute=available_dt.minute,
                second=0,
                microsecond=0,
            )
            if available_dt > reference_time:
                return {
                    "eligible": False,
                    "reason": f"Crew is available only from {available_from}.",
                }

    return {
        "eligible": True,
        "reason": "Crew status is AVAILABLE.",
    }


def _is_qualified(crew: Dict[str, Any], flight: Dict[str, Any]) -> Dict[str, Any]:
    qualification = str(crew.get("qualification") or "")
    aircraft_type = str(flight.get("aircraft") or "")

    if not qualification:
        return {
            "eligible": False,
            "reason": "Qualification data is missing.",
        }

    if aircraft_type not in qualification:
        return {
            "eligible": False,
            "reason": f"Crew qualification {qualification} does not include aircraft {aircraft_type}.",
        }

    return {
        "eligible": True,
        "reason": f"Aircraft qualification matches {aircraft_type}.",
    }


def _is_duty_legal(crew: Dict[str, Any], reference_time: datetime) -> Dict[str, Any]:
    duty_start = crew.get("duty_start")
    if not duty_start:
        return {
            "eligible": True,
            "status": "REVIEW_REQUIRED",
            "reason": "Duty start missing; manual review required before assignment.",
        }

    duty_start_dt = _parse_time(duty_start)
    if duty_start_dt is None:
        return {
            "eligible": True,
            "status": "REVIEW_REQUIRED",
            "reason": "Duty start is not in the expected HH:MM format.",
        }

    duty_start_dt = reference_time.replace(
        hour=duty_start_dt.hour,
        minute=duty_start_dt.minute,
        second=0,
        microsecond=0,
    )

    if duty_start_dt > reference_time:
        duty_start_dt -= timedelta(days=1)

    elapsed_hours = (reference_time - duty_start_dt).total_seconds() / 3600
    remaining_hours = DEFAULT_MAX_DUTY_HOURS - elapsed_hours

    if remaining_hours <= 0:
        return {
            "eligible": False,
            "status": "LIMIT_REACHED",
            "reason": f"Duty limit reached; only {max(remaining_hours, 0):.1f} hours remain.",
        }

    if remaining_hours <= 1:
        return {
            "eligible": False,
            "status": "HIGH_RISK",
            "reason": f"Duty risk is high; only {remaining_hours:.1f} hours remain.",
        }

    return {
        "eligible": True,
        "status": "OK",
        "reason": f"Duty is within the prototype limit; {remaining_hours:.1f} hours remain.",
    }


def _is_location_compatible(crew: Dict[str, Any], flight: Dict[str, Any]) -> Dict[str, Any]:
    crew_base = (crew.get("base") or "").upper()
    flight_origin = (flight.get("origin") or "").upper()

    if crew_base == flight_origin:
        return {
            "eligible": True,
            "status": "READY_AT_BASE",
            "reason": "Crew base matches the flight origin.",
        }

    return {
        "eligible": True,
        "status": "POSITIONING_REQUIRED",
        "reason": f"Crew base {crew_base} differs from flight origin {flight_origin}; positioning would be required.",
    }


def _has_schedule_conflict(crew_id: str, flight_id: str) -> Dict[str, Any]:
    assignments = load_assignments()
    flight_map = {flight["flight_id"]: flight for flight in load_flights()}

    current_flight = flight_map.get(flight_id)
    if current_flight is None:
        return {
            "eligible": True,
            "status": "NO_CONFLICT",
            "reason": "Flight was not found; no schedule conflict check could be completed.",
        }

    current_departure = _parse_time(current_flight.get("estimated_departure") or current_flight.get("scheduled_departure"))
    if current_departure is None:
        return {
            "eligible": True,
            "status": "NO_CONFLICT",
            "reason": "Flight departure time is missing; no time-based conflict could be detected.",
        }

    existing_conflicts = []
    for assignment in assignments:
        if assignment.get("crew_id") != crew_id:
            continue
        if assignment.get("flight_id") == flight_id:
            continue

        other_flight = flight_map.get(assignment.get("flight_id"))
        if not other_flight:
            continue

        other_departure = _parse_time(other_flight.get("estimated_departure") or other_flight.get("scheduled_departure"))
        if other_departure is None:
            continue

        if abs((other_departure - current_departure).total_seconds()) < 1800:
            existing_conflicts.append({
                "flight_id": assignment.get("flight_id"),
                "departure": other_flight.get("estimated_departure") or other_flight.get("scheduled_departure"),
            })

    if existing_conflicts:
        return {
            "eligible": False,
            "status": "CONFLICT",
            "reason": "Candidate already has another assignment close to the target departure time.",
            "conflicting_flights": existing_conflicts,
        }

    return {
        "eligible": True,
        "status": "NO_CONFLICT",
        "reason": "No nearby assignment conflict was detected.",
    }


def evaluate_candidate_for_replacement(crew_id: str, flight_id: str, role: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
    reference = _reference_time(reference_time)
    flight = get_flight(flight_id)
    if flight is None:
        return {
            "crew_id": crew_id,
            "status": "REJECTED",
            "reason": "Flight not found.",
        }

    crew = next((person for person in load_crew() if person["crew_id"] == crew_id), None)
    if crew is None:
        return {
            "crew_id": crew_id,
            "status": "REJECTED",
            "reason": "Crew record not found.",
        }

    if _normalize_role(crew.get("role")) != _normalize_role(role):
        return {
            "crew_id": crew_id,
            "status": "REJECTED",
            "reason": f"Crew role {crew.get('role')} does not match required role {role}.",
        }

    checks = {
        "availability": _is_crew_available(crew, reference),
        "qualification": _is_qualified(crew, flight),
        "duty": _is_duty_legal(crew, reference),
        "location": _is_location_compatible(crew, flight),
        "schedule": _has_schedule_conflict(crew_id, flight_id),
    }

    rejected_reasons = []
    for check_name, check_result in checks.items():
        if check_name in {"availability", "qualification", "duty", "schedule"}:
            if check_result.get("eligible") is False:
                rejected_reasons.append(check_result.get("reason", f"{check_name} failed."))

    location_status = checks["location"]["status"]

    if rejected_reasons:
        status = "REJECTED"
        recommendation_status = "REJECTED"
        reasons = rejected_reasons
    else:
        status = "ELIGIBLE"
        recommendation_status = "READY" if location_status == "READY_AT_BASE" else "POSITIONING_REQUIRED"
        reasons = [checks["location"]["reason"], checks["duty"]["reason"], checks["schedule"]["reason"]]

    return {
        "crew_id": crew_id,
        "name": crew.get("name"),
        "role": crew.get("role"),
        "base": crew.get("base"),
        "qualification": crew.get("qualification"),
        "status": status,
        "recommendation_status": recommendation_status,
        "location_status": location_status,
        "checks": checks,
        "reasons": reasons,
    }


def find_eligible_replacements(flight_id: str, role: str, reference_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
    flight = get_flight(flight_id)
    if flight is None:
        return []

    options = []
    normalized_role = _normalize_role(role)
    for crew in load_crew():
        if _normalize_role(crew.get("role")) != normalized_role:
            continue
        if (crew.get("status") or "").upper() != "AVAILABLE":
            continue

        result = evaluate_candidate_for_replacement(crew["crew_id"], flight_id, role, reference_time=reference_time)
        if result["status"] == "ELIGIBLE":
            result["target_flight"] = flight_id
            result["target_origin"] = flight.get("origin")
            options.append(result)

    options.sort(
        key=lambda item: (
            0 if item["location_status"] == "READY_AT_BASE" else 1,
            item["crew_id"],
        )
    )
    return options


def generate_recovery_options(flight_id: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
    flight = get_flight(flight_id)
    if flight is None:
        return {
            "status": "REVIEW_REQUIRED",
            "summary": "Flight not found.",
            "recommended_candidate": None,
            "role_breakdown": {},
        }

    assigned_crew = get_flight_crew(flight_id)
    role_breakdown: Dict[str, List[Dict[str, Any]]] = {}
    unresolved_roles: List[str] = []
    all_candidates: List[Dict[str, Any]] = []

    for assignment in assigned_crew:
        required_role = assignment.get("assignment_role") or "UNKNOWN"
        candidates = find_eligible_replacements(flight_id, required_role, reference_time=reference_time)
        role_breakdown[required_role] = candidates
        if not candidates:
            unresolved_roles.append(required_role)
        all_candidates.extend(candidates)

    if all_candidates:
        recommended = min(
            all_candidates,
            key=lambda item: (0 if item["recommendation_status"] == "READY" else 1, item["crew_id"]),
        )
        status = "RECOVERY_OPTIONS_AVAILABLE"
        if unresolved_roles:
            status = "RECOVERY_GAPS_PRESENT"
    else:
        recommended = None
        status = "NO_CLEAN_RECOVERY_OPTIONS"

    summary = {
        "flight_id": flight_id,
        "route": f"{flight.get('origin')} -> {flight.get('destination')}",
        "affected_roles": sorted({assignment.get('assignment_role') for assignment in assigned_crew}),
        "eligible_candidate_count": len(all_candidates),
        "unresolved_roles": unresolved_roles,
    }

    return {
        "status": status,
        "recommended_candidate": recommended,
        "role_breakdown": role_breakdown,
        "summary": summary,
        "unresolved_roles": unresolved_roles,
    }


def analyze_disruption(flight_id: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
    reference = _reference_time(reference_time)
    flight = get_flight(flight_id)
    if flight is None:
        return {
            "flight_id": flight_id,
            "status": "NOT_FOUND",
            "message": "Flight not found.",
        }

    affected_crew = get_flight_crew(flight_id)
    downstream = get_downstream_flights(flight_id)
    role_candidates: Dict[str, List[Dict[str, Any]]] = {}
    for assignment in affected_crew:
        role = assignment.get("assignment_role") or "UNKNOWN"
        role_candidates[role] = find_eligible_replacements(flight_id, role, reference_time=reference)

    recommendation = generate_recovery_options(flight_id, reference_time=reference)

    if recommendation["recommended_candidate"]:
        selected = recommendation["recommended_candidate"]
        recommended_action = {
            "crew_id": selected["crew_id"],
            "name": selected["name"],
            "role": selected["role"],
            "message": f"Assign {selected['crew_id']} to {flight_id} as a replacement for the affected {selected['role']} role.",
            "status": selected["recommendation_status"],
        }
    else:
        recommended_action = {
            "crew_id": None,
            "name": None,
            "role": None,
            "message": "No eligible replacement was found. Escalate to crew lead and verify whether a standby or repositioning option is available.",
            "status": "NO_CANDIDATE",
        }

    return {
        "flight_id": flight_id,
        "flight": flight,
        "affected_crew": affected_crew,
        "eligible_replacements": role_candidates,
        "downstream_impact": downstream,
        "recommendation": recommendation,
        "recommended_action": recommended_action,
    }


def build_crew_lead_report(flight_id: str, reference_time: Optional[datetime] = None) -> Dict[str, Any]:
    analysis = analyze_disruption(flight_id, reference_time=reference_time)

    if analysis.get("status") == "NOT_FOUND":
        return {
            "flight_id": flight_id,
            "status": "NOT_FOUND",
            "message": "Flight not found.",
        }

    recommended = analysis.get("recommended_action", {})
    recommendation = analysis.get("recommendation", {})
    role_candidates = analysis.get("eligible_replacements", {})

    report = {
        "flight_id": flight_id,
        "status": recommendation.get("status", "REVIEW_REQUIRED"),
        "summary": {
            "route": f"{analysis['flight'].get('origin')} -> {analysis['flight'].get('destination')}",
            "delay_minutes": analysis['flight'].get('delay_minutes', 0),
            "status": analysis['flight'].get('status', 'UNKNOWN'),
            "affected_crew_count": len(analysis.get("affected_crew", [])),
            "eligible_candidate_count": recommendation.get("summary", {}).get("eligible_candidate_count", 0),
        },
        "key_findings": [
            f"Flight {flight_id} is currently {analysis['flight'].get('status', 'UNKNOWN')}.",
            f"Crew impact includes {len(analysis.get('affected_crew', []))} assigned crew members.",
            f"Downstream impact includes {len(analysis.get('downstream_impact', []))} later crew-linked flight entries.",
        ],
        "recommended_action": recommended,
        "alternatives_by_role": {
            role: [
                {
                    "crew_id": candidate["crew_id"],
                    "name": candidate.get("name"),
                    "recommendation_status": candidate.get("recommendation_status"),
                    "location_status": candidate.get("location_status"),
                }
                for candidate in candidates
            ]
            for role, candidates in role_candidates.items()
        },
        "crew_lead_note": (
            "This is decision-support information only. "
            "No crew reassignment has been executed automatically."
        ),
    }

    if recommendation.get("recommended_candidate"):
        selected = recommendation["recommended_candidate"]
        report["recommended_action"]["message"] = (
            f"Assign {selected['crew_id']} to {flight_id} as the preferred replacement "
            f"for the affected {selected['role']} role."
        )

    return report

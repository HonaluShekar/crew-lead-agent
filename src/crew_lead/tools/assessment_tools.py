from .flight_tools import get_flight
from .assignment_tools import get_flight_crew
from .duty_tools import check_duty_risk
from .recovery_tools import evaluate_recovery_candidates
from .impact_tools import get_downstream_flights


def complete_disruption_assessment(flight_id):
    """
    Build a complete operational assessment for a disrupted flight.

    This function gathers deterministic operational information
    and calculates an overall prototype operational priority.

    It does not make the final operational decision.
    """

    flight = get_flight(flight_id)

    if flight is None:
        return {
            "flight_id": flight_id,
            "error": "FLIGHT_NOT_FOUND"
        }

    assignments = get_flight_crew(flight_id)

    crew_assessment = []
    required_roles = set()

    for assignment in assignments:

        crew_id = assignment["crew_id"]

        duty_risk = check_duty_risk(
            crew_id
        )

        actual_crew_role = duty_risk.get(
            "role",
            assignment["assignment_role"]
        )

        crew_assessment.append({
            "crew_id": crew_id,
            "assignment_role": assignment["assignment_role"],
            "actual_crew_role": actual_crew_role,
            "duty_risk": duty_risk
        })

        required_roles.add(
            actual_crew_role
        )

    replacement_options = []

    for required_role in required_roles:

        evaluation = evaluate_recovery_candidates(
            flight_id,
            required_role
        )

        replacement_options.append(
            evaluation
        )

    downstream = get_downstream_flights(
        flight_id
    )

    # ========================================================
    # CALCULATE OVERALL OPERATIONAL PRIORITY
    # ========================================================

    limit_reached_count = 0
    high_risk_count = 0

    for crew in crew_assessment:

        risk = crew["duty_risk"].get(
            "risk"
        )

        if risk == "LIMIT_REACHED":
            limit_reached_count += 1

        elif risk == "HIGH":
            high_risk_count += 1

    conflict_count = 0
    positioning_count = 0
    no_candidate_roles = 0

    for evaluation in replacement_options:

        if evaluation["candidates_found"] == 0:
            no_candidate_roles += 1

        for candidate in evaluation["candidates"]:

            status = candidate.get(
                "recommendation_status"
            )

            if status == "CONFLICT":
                conflict_count += 1

            elif status == "POSITIONING_REQUIRED":
                positioning_count += 1

    delayed_downstream_count = sum(
        1
        for flight_info in downstream
        if flight_info.get("status") == "DELAYED"
    )

    # ========================================================
    # PRIORITY RULES
    # ========================================================

    if limit_reached_count > 0 and no_candidate_roles > 0:
        operational_priority = "CRITICAL"
        priority_score = 1

    elif limit_reached_count >= 2:
        operational_priority = "HIGH"
        priority_score = 2

    elif limit_reached_count == 1:
        operational_priority = "HIGH"
        priority_score = 2

    elif high_risk_count > 0:
        operational_priority = "MEDIUM"
        priority_score = 3

    elif positioning_count > 0:
        operational_priority = "MEDIUM"
        priority_score = 3

    else:
        operational_priority = "LOW"
        priority_score = 4

    # ========================================================
    # ADDITIONAL OPERATIONAL FLAGS
    # ========================================================

    operational_flags = []

    if limit_reached_count > 0:
        operational_flags.append(
            "CREW_DUTY_LIMIT_REACHED"
        )

    if no_candidate_roles > 0:
        operational_flags.append(
            "ROLE_WITH_NO_REPLACEMENT_CANDIDATE"
        )

    if positioning_count > 0:
        operational_flags.append(
            "POSITIONING_REQUIRED"
        )

    if conflict_count > 0:
        operational_flags.append(
            "REPLACEMENT_ASSIGNMENT_CONFLICTS"
        )

    if delayed_downstream_count > 0:
        operational_flags.append(
            "DOWNSTREAM_DELAY_PRESENT"
        )

    return {
        "flight": flight,

        "operational_priority": {
            "level": operational_priority,
            "score": priority_score,
            "reason": (
                "Prototype priority based on crew duty risk, "
                "replacement availability, positioning "
                "requirements, conflicts, and downstream impact."
            )
        },

        "operational_flags": operational_flags,

        "assigned_crew": crew_assessment,

        "replacement_options": replacement_options,

        "downstream_impact": downstream,

        "assessment_summary": {
            "limit_reached_crew_count": limit_reached_count,
            "high_risk_crew_count": high_risk_count,
            "replacement_conflict_count": conflict_count,
            "positioning_required_count": positioning_count,
            "roles_without_candidates": no_candidate_roles,
            "delayed_downstream_flight_count": delayed_downstream_count
        }
    }
from .replacement_tools import find_replacement_crew
from .candidate_tools import get_candidate_conflicts
from .positioning_tools import assess_positioning


def evaluate_recovery_candidates(flight_id, role):
    """
    Evaluate potential replacement crew for a disrupted flight.

    This combines:
    - replacement search
    - assignment conflict checks
    - positioning assessment

    Results are decision-support information only.
    """

    candidates = find_replacement_crew(
        flight_id,
        role
    )

    evaluated = []

    for candidate in candidates:

        crew_id = candidate["crew_id"]

        conflicts = get_candidate_conflicts(
            crew_id,
            flight_id
        )

        positioning = assess_positioning(
            crew_id,
            flight_id
        )

        # Determine recommendation status.
        if conflicts:
            recommendation_status = "CONFLICT"
            recovery_priority = 3

        elif positioning["status"] == "READY_AT_BASE":
            recommendation_status = "READY"
            recovery_priority = 1

        elif positioning["status"] == "POSITIONING_REQUIRED":
            recommendation_status = "POSITIONING_REQUIRED"
            recovery_priority = 2

        else:
            recommendation_status = "REVIEW_REQUIRED"
            recovery_priority = 4

        evaluated.append({
            **candidate,
            "conflicts": conflicts,
            "positioning": positioning,
            "recommendation_status": recommendation_status,
            "recovery_priority": recovery_priority
        })

    # Sort candidates from strongest recovery option
    # to weakest.
    evaluated.sort(
        key=lambda candidate: candidate["recovery_priority"]
    )

    return {
        "flight_id": flight_id,
        "role": role,
        "candidates_found": len(evaluated),
        "candidates": evaluated
    }
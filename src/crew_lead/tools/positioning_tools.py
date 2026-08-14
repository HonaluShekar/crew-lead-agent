from .data_loader import load_crew
from .flight_tools import get_flight
from .candidate_tools import get_candidate_conflicts


def assess_positioning(crew_id, target_flight_id):
    """
    Assess the basic positioning requirement for a replacement crew member.

    This is a prototype classification and does not calculate actual
    travel time or regulatory legality.
    """

    crew = load_crew()
    flight = get_flight(target_flight_id)

    member = next(
        (person for person in crew if person["crew_id"] == crew_id),
        None
    )

    if member is None:
        return {
            "crew_id": crew_id,
            "status": "CREW_NOT_FOUND"
        }

    if flight is None:
        return {
            "crew_id": crew_id,
            "status": "FLIGHT_NOT_FOUND"
        }

    conflicts = get_candidate_conflicts(
        crew_id,
        target_flight_id
    )

    if conflicts:
        return {
            "crew_id": crew_id,
            "base": member["base"],
            "target_airport": flight["origin"],
            "status": "CONFLICT",
            "conflicting_flights": conflicts
        }

    if member["base"] == flight["origin"]:
        return {
            "crew_id": crew_id,
            "base": member["base"],
            "target_airport": flight["origin"],
            "status": "READY_AT_BASE",
            "conflicting_flights": []
        }

    return {
        "crew_id": crew_id,
        "base": member["base"],
        "target_airport": flight["origin"],
        "status": "POSITIONING_REQUIRED",
        "conflicting_flights": []
    }
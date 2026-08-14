from .data_loader import load_crew, load_assignments
from .flight_tools import get_flight


def find_replacement_crew(flight_id, role):
    """
    Find potential replacement crew for a flight.

    Candidates are grouped by:
    1. Same-base available crew
    2. Other-base available crew

    This is a prototype recovery search.
    Final legality and operational approval must be checked separately.
    """

    flight = get_flight(flight_id)

    if flight is None:
        return []

    required_aircraft = flight["aircraft"]
    origin = flight["origin"]

    crew = load_crew()
    assignments = load_assignments()

    # Find crew members already assigned to flights.
    assigned_crew_ids = {
        assignment["crew_id"]
        for assignment in assignments
    }

    candidates = []

    for member in crew:

        # Correct role
        if member["role"] != role:
            continue

        # Must be available
        if member["status"] != "AVAILABLE":
            continue

        # Must be qualified for the aircraft
        if required_aircraft not in member["qualification"]:
            continue

        if member["base"] == origin:
            priority = 1
            location_type = "SAME_BASE"
        else:
            priority = 2
            location_type = "OTHER_BASE"

        candidates.append({
            "crew_id": member["crew_id"],
            "name": member["name"],
            "role": member["role"],
            "base": member["base"],
            "qualification": member["qualification"],
            "status": member["status"],
            "priority": priority,
            "location_type": location_type,
            "already_assigned": member["crew_id"] in assigned_crew_ids
        })

    # Same-base candidates first.
    candidates.sort(key=lambda candidate: candidate["priority"])

    return candidates
from .data_loader import load_assignments


def get_candidate_conflicts(crew_id, target_flight_id):
    """
    Find existing assignments for a potential replacement crew member.

    The result identifies possible operational conflicts.
    It does not determine legal feasibility.
    """

    assignments = load_assignments()

    conflicts = []

    for assignment in assignments:

        if assignment["crew_id"] != crew_id:
            continue

        if assignment["flight_id"] == target_flight_id:
            continue

        conflicts.append({
            "flight_id": assignment["flight_id"],
            "assignment_role": assignment["assignment_role"]
        })

    return conflicts
from .data_loader import load_assignments


def get_flight_crew(flight_id):
    """Return all crew members assigned to a flight."""

    assignments = load_assignments()

    return [
        assignment
        for assignment in assignments
        if assignment["flight_id"] == flight_id
    ]
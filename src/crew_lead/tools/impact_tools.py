from datetime import datetime

from .data_loader import (
    load_assignments,
    load_flights,
    load_crew,
)


def _flight_time(time_string):
    """Convert HH:MM into a comparable datetime value."""
    return datetime.strptime(time_string, "%H:%M")


def get_crew_flights(crew_id):
    """Find all flights assigned to a crew member."""

    assignments = load_assignments()

    return [
        assignment
        for assignment in assignments
        if assignment["crew_id"] == crew_id
    ]


def get_downstream_flights(flight_id):
    """
    Find flights departing after the given flight
    that use any of the same crew members.

    The result includes both:
    - assignment_role from assignments.csv
    - actual crew role from crew.csv
    """

    assignments = load_assignments()
    flights = load_flights()
    crew_members = load_crew()

    flight_map = {
        flight["flight_id"]: flight
        for flight in flights
    }

    crew_map = {
        crew["crew_id"]: crew
        for crew in crew_members
    }

    current_flight = flight_map.get(flight_id)

    if current_flight is None:
        return []

    current_crew = {
        assignment["crew_id"]
        for assignment in assignments
        if assignment["flight_id"] == flight_id
    }

    current_departure = _flight_time(
        current_flight["estimated_departure"]
    )

    downstream = []

    for assignment in assignments:

        if assignment["crew_id"] not in current_crew:
            continue

        if assignment["flight_id"] == flight_id:
            continue

        other_flight = flight_map.get(
            assignment["flight_id"]
        )

        if other_flight is None:
            continue

        other_departure = _flight_time(
            other_flight["estimated_departure"]
        )

        if other_departure > current_departure:

            crew_member = crew_map.get(
                assignment["crew_id"]
            )

            actual_crew_role = None

            if crew_member is not None:
                actual_crew_role = crew_member.get("role")

            downstream.append({
                "flight_id": other_flight["flight_id"],
                "crew_id": assignment["crew_id"],
                "assignment_role": assignment["assignment_role"],
                "actual_crew_role": actual_crew_role,
                "estimated_departure": other_flight[
                    "estimated_departure"
                ],
                "status": other_flight["status"],
            })

    return downstream

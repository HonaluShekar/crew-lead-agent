from .data_loader import load_crew


def get_crew(crew_id):
    """Find a crew member by crew ID."""

    crew = load_crew()

    for member in crew:
        if member["crew_id"] == crew_id:
            return member

    return None
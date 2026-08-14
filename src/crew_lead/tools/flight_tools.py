from .data_loader import load_flights


def get_flight(flight_id):
    """Find a flight by flight ID."""

    flights = load_flights()

    for flight in flights:
        if flight["flight_id"] == flight_id:
            return flight

    return None
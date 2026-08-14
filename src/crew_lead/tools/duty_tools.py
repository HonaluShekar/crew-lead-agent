from datetime import datetime, timedelta

from .crew_tools import get_crew


def check_duty_risk(crew_id, max_duty_hours=8):
    """
    Check the current duty-time risk for a crew member.

    max_duty_hours is a configurable prototype threshold.
    It is NOT an airline regulatory limit.
    """

    crew_member = get_crew(crew_id)

    if crew_member is None:
        return {
            "crew_id": crew_id,
            "status": "NOT_FOUND"
        }

    duty_start_str = crew_member["duty_start"]

    if not duty_start_str:
        return {
            "crew_id": crew_id,
            "name": crew_member["name"],
            "role": crew_member["role"],
            "status": "DUTY_START_NOT_AVAILABLE",
            "risk": "REVIEW_REQUIRED"
        }

    now = datetime.now()

    duty_start = datetime.strptime(
        duty_start_str,
        "%H:%M"
    )

    duty_start = now.replace(
        hour=duty_start.hour,
        minute=duty_start.minute,
        second=0,
        microsecond=0
    )

    # Handle a duty start that belongs to the previous day.
    if duty_start > now:
        duty_start -= timedelta(days=1)

    elapsed_hours = (
        now - duty_start
    ).total_seconds() / 3600

    remaining_hours = max_duty_hours - elapsed_hours

    if remaining_hours <= 0:
        risk = "LIMIT_REACHED"
        priority = 1

    elif remaining_hours <= 1:
        risk = "HIGH"
        priority = 2

    elif remaining_hours <= 2:
        risk = "MEDIUM"
        priority = 3

    else:
        risk = "LOW"
        priority = 4

    return {
        "crew_id": crew_id,
        "name": crew_member["name"],
        "role": crew_member["role"],
        "duty_start": duty_start_str,
        "elapsed_hours": round(elapsed_hours, 2),
        "max_duty_hours": max_duty_hours,
        "remaining_hours": round(
            max(remaining_hours, 0),
            2
        ),
        "risk": risk,
        "priority": priority
    }
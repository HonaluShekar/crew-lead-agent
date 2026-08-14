def build_recovery_recommendation(assessment):
    """
    Build a deterministic recovery recommendation from a
    completed crew disruption assessment.

    This function does not execute any operational change.
    It only compares the available recovery options.
    """

    if not assessment:
        return {
            "status": "REVIEW_REQUIRED",
            "reason": "No assessment data available."
        }

    if "error" in assessment:
        return {
            "status": "REVIEW_REQUIRED",
            "reason": assessment["error"]
        }

    replacement_options = assessment.get(
        "replacement_options",
        []
    )

    recovery_options = []
    blocked_options = []
    unresolved_roles = []

    for role_assessment in replacement_options:

        role = role_assessment.get("role")

        candidates = role_assessment.get(
            "candidates",
            []
        )

        # No candidates for this role.
        if not candidates:
            unresolved_roles.append(role)
            continue

        for candidate in candidates:

            status = candidate.get(
                "recommendation_status",
                "REVIEW_REQUIRED"
            )

            candidate_info = {
                "crew_id": candidate.get("crew_id"),
                "name": candidate.get("name"),
                "role": role,
                "qualification": candidate.get(
                    "qualification"
                ),
                "status": candidate.get(
                    "status"
                ),
                "base": candidate.get(
                    "base"
                ),
                "recommendation_status": status,
                "recovery_priority": candidate.get(
                    "recovery_priority"
                ),
                "conflicts": candidate.get(
                    "conflicts",
                    []
                ),
                "positioning": candidate.get(
                    "positioning"
                ),
            }

            # Candidates with conflicts are blocked.
            if status == "CONFLICT":
                blocked_options.append(
                    candidate_info
                )

            # These candidates remain potential options.
            elif status in (
                "READY",
                "POSITIONING_REQUIRED",
                "REVIEW_REQUIRED",
            ):
                recovery_options.append(
                    candidate_info
                )

    # Rank potential recovery options.
    #
    # READY candidates are preferred first.
    # POSITIONING_REQUIRED candidates come next.
    # REVIEW_REQUIRED candidates come last.
    status_order = {
        "READY": 1,
        "POSITIONING_REQUIRED": 2,
        "REVIEW_REQUIRED": 3,
    }

    recovery_options.sort(
        key=lambda candidate: (
            status_order.get(
                candidate["recommendation_status"],
                99
            ),
            candidate["recovery_priority"]
            if candidate["recovery_priority"] is not None
            else 99,
        )
    )

    # Determine overall recovery status.
    if unresolved_roles:
        overall_status = "RECOVERY_GAPS_PRESENT"

    elif recovery_options:
        overall_status = "RECOVERY_OPTIONS_AVAILABLE"

    else:
        overall_status = "NO_CLEAN_RECOVERY_OPTIONS"

    return {
        "status": overall_status,
        "potential_recovery_options": recovery_options,
        "blocked_options": blocked_options,
        "unresolved_roles": unresolved_roles,
        "note": (
            "These are decision-support options only. "
            "No crew assignment or operational change "
            "has been executed."
        ),
    }


def build_crew_lead_action_plan(assessment):
    """
    Convert the recovery assessment into a clear Crew Lead
    action plan.

    This function provides decision support only.
    It does not execute crew or flight changes.
    """

    recommendation = build_recovery_recommendation(
        assessment
    )

    actions = []

    # ---------------------------------------------------------
    # 1. Unresolved roles
    # ---------------------------------------------------------

    unresolved_roles = recommendation.get(
        "unresolved_roles",
        []
    )

    for role in unresolved_roles:

        actions.append({
            "priority": 1,
            "action": "FIND_ALTERNATIVE_CREW",
            "role": role,
            "reason": (
                "No replacement candidates were found "
                "for this role."
            )
        })

    # ---------------------------------------------------------
    # 2. Positioning-required candidates
    # ---------------------------------------------------------

    positioning_candidates = [
        candidate
        for candidate in recommendation.get(
            "potential_recovery_options",
            []
        )
        if candidate.get(
            "recommendation_status"
        ) == "POSITIONING_REQUIRED"
    ]

    for candidate in positioning_candidates:

        positioning = candidate.get(
            "positioning",
            {}
        )

        actions.append({
            "priority": 2,
            "action": "VERIFY_POSITIONING",
            "crew_id": candidate.get("crew_id"),
            "name": candidate.get("name"),
            "role": candidate.get("role"),
            "base": candidate.get("base"),
            "target_airport": positioning.get(
                "target_airport"
            ),
            "reason": (
                "Candidate has no detected assignment "
                "conflict, but positioning feasibility "
                "must be verified."
            )
        })

    # ---------------------------------------------------------
    # 3. Blocked candidates
    # ---------------------------------------------------------

    blocked_candidates = recommendation.get(
        "blocked_options",
        []
    )

    for candidate in blocked_candidates:

        actions.append({
            "priority": 3,
            "action": "DO_NOT_USE_UNLESS_CONFLICT_RESOLVED",
            "crew_id": candidate.get("crew_id"),
            "name": candidate.get("name"),
            "role": candidate.get("role"),
            "conflicts": candidate.get(
                "conflicts",
                []
            ),
            "reason": (
                "Candidate has existing assignment "
                "conflicts."
            )
        })

    # ---------------------------------------------------------
    # 4. Downstream impact
    # ---------------------------------------------------------

    downstream = assessment.get(
        "downstream_impact",
        []
    )

    delayed_downstream = [
        flight
        for flight in downstream
        if flight.get("status") == "DELAYED"
    ]

    if delayed_downstream:

        actions.append({
            "priority": 2,
            "action": "REVIEW_DOWNSTREAM_IMPACT",
            "flights": delayed_downstream,
            "reason": (
                "One or more downstream flights are "
                "already delayed."
            )
        })

    # ---------------------------------------------------------
    # 5. Determine overall action status
    # ---------------------------------------------------------

    if unresolved_roles:

        overall_status = (
            "ACTION_REQUIRED_WITH_RECOVERY_GAP"
        )

    elif positioning_candidates:

        overall_status = (
            "POSITIONING_VERIFICATION_REQUIRED"
        )

    else:

        overall_status = (
            "CREW_LEAD_REVIEW_REQUIRED"
        )

    # Keep highest-priority actions first.
    actions.sort(
        key=lambda action: action.get(
            "priority",
            99
        )
    )

    return {
        "status": overall_status,
        "actions": actions,
        "decision_authority": "CREW_LEAD",
        "execution_performed": False,
        "note": (
            "This action plan provides decision support only. "
            "No crew assignment, flight change, or positioning "
            "has been executed."
        )
    }
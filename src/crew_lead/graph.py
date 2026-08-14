from __future__ import annotations

from typing import Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph

from .workflow import analyze_disruption


class CrewLeadState(TypedDict, total=False):
    flight_id: str
    disruption: str
    affected_crew: list
    eligible_replacements: dict
    downstream_impact: list
    recommendation: dict
    recommended_action: dict
    summary: dict


def understand_disruption(state: CrewLeadState) -> CrewLeadState:
    flight_id = state.get("flight_id")
    disruption = state.get("disruption") or "Crew disruption assessment requested."
    return {
        **state,
        "flight_id": flight_id,
        "disruption": disruption,
    }


def identify_affected_crew(state: CrewLeadState) -> CrewLeadState:
    flight_id = state.get("flight_id")
    if not flight_id:
        return {**state, "affected_crew": []}

    analysis = analyze_disruption(flight_id)
    return {
        **state,
        "affected_crew": analysis.get("affected_crew", []),
    }


def evaluate_crew_constraints(state: CrewLeadState) -> CrewLeadState:
    flight_id = state.get("flight_id")
    if not flight_id:
        return {**state, "eligible_replacements": {}, "downstream_impact": []}

    analysis = analyze_disruption(flight_id)
    return {
        **state,
        "eligible_replacements": analysis.get("eligible_replacements", {}),
        "downstream_impact": analysis.get("downstream_impact", []),
    }


def generate_recommendation(state: CrewLeadState) -> CrewLeadState:
    flight_id = state.get("flight_id")
    if not flight_id:
        return {**state, "recommendation": {"status": "REVIEW_REQUIRED"}, "recommended_action": {"status": "NO_CANDIDATE"}}

    analysis = analyze_disruption(flight_id)
    recommendation = analysis.get("recommendation", {})
    recommended_action = analysis.get("recommended_action", {})
    summary = {
        "flight_id": flight_id,
        "status": recommendation.get("status"),
        "eligible_candidate_count": recommendation.get("summary", {}).get("eligible_candidate_count", 0),
    }

    return {
        **state,
        "recommendation": recommendation,
        "recommended_action": recommended_action,
        "summary": summary,
    }


def build_crew_lead_graph():
    workflow = StateGraph(CrewLeadState)
    workflow.add_node("understand_disruption", understand_disruption)
    workflow.add_node("identify_affected_crew", identify_affected_crew)
    workflow.add_node("evaluate_crew_constraints", evaluate_crew_constraints)
    workflow.add_node("generate_recommendation", generate_recommendation)

    workflow.add_edge(START, "understand_disruption")
    workflow.add_edge("understand_disruption", "identify_affected_crew")
    workflow.add_edge("identify_affected_crew", "evaluate_crew_constraints")
    workflow.add_edge("evaluate_crew_constraints", "generate_recommendation")
    workflow.add_edge("generate_recommendation", END)

    return workflow.compile()


crew_lead_graph = build_crew_lead_graph()

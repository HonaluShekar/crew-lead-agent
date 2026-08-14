from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.crew_lead.agent import agent
from src.crew_lead.workflow import analyze_disruption, build_crew_lead_report


app = FastAPI(
    title="Crew Lead Agent",
    description="Airline crew disruption decision-support backend",
    version="1.0.0",
)


class AskRequest(BaseModel):
    message: str


@app.get("/")
def root():
    return {
        "status": "Crew Lead Agent API is running",
        "service": "crew-lead-agent",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/assess/{flight_id}")
def assess_flight(flight_id: str):
    """
    Run the deterministic crew disruption assessment
    and recovery recommendation for a flight.
    """

    report = build_crew_lead_report(flight_id)

    if report.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=404,
            detail="No assessment data available for this flight.",
        )

    return {
        "flight_id": flight_id,
        "assessment": report,
        "decision_authority": "CREW_LEAD",
        "execution_performed": False,
    }


@app.post("/ask")
def ask(request: AskRequest):
    """
    Natural-language interface to the Crew Lead Agent.
    """

    message = (request.message or "").strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail="A non-empty message is required.",
        )

    try:
        lowered = message.lower()

        if "assess" in lowered or "disruption" in lowered or "flight" in lowered:
            flight_id = None
            for token in message.split():
                token = token.strip(".,!?;:")
                if token.startswith("6E") or token.startswith("AI"):
                    flight_id = token
                    break

            if flight_id:
                report = build_crew_lead_report(flight_id)
                return {
                    "response": report,
                    "flight_id": flight_id,
                    "decision_authority": "CREW_LEAD",
                    "execution_performed": False,
                }

        response = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message,
                    }
                ]
            }
        )

        return {
            "response": response["messages"][-1].content
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
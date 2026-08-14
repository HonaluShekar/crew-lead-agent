from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import logging
import re
from functools import lru_cache
from typing import Optional

from src.crew_lead.ui_adapter import (
    build_ui_activity,
    build_ui_analysis,
    build_ui_crew,
    build_ui_disruptions,
    build_ui_flights,
    build_ui_issues,
    build_ui_recommendations,
    build_ui_snapshot,
)
from src.crew_lead.workflow import build_crew_lead_report


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Crew Lead Agent API",
    description="Airline crew disruption decision-support backend",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# Allows the Bolt/Vite frontend to communicate with FastAPI
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request models for endpoints
# ---------------------------------------------------------
class CrewLeadRequest(BaseModel):
    message: str
    
    @validator("message")
    def validate_message(cls, v):
        if len(v) > 10000:
            raise ValueError("Message is too long (max 10000 characters)")
        return v.strip()


class UIAnalysisRequest(BaseModel):
    query: str

    @validator("query")
    def query_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


@lru_cache(maxsize=1)
def _load_optional_agent():
    """Load the LLM agent only when the natural-language fallback is used."""

    try:
        from src.crew_lead.agent import agent

        return agent
    except Exception as exc:
        logger.warning("LLM agent unavailable: %s", exc)
        return None


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def validate_flight_id(flight_id: str) -> str:
    """
    Validate and normalize flight ID.
    
    Raises:
        HTTPException if flight_id is invalid
    """
    if not flight_id or not flight_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Flight ID cannot be empty"
        )
    
    flight_id = flight_id.strip().upper()
    
    # Allow alphanumeric + some special chars common in flight codes
    if not re.match(r'^[A-Z0-9\-\.]{2,20}$', flight_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid flight ID format"
        )
    
    return flight_id


def validate_assessment_response(report: dict) -> dict:
    """
    Validate that assessment response has required structure.
    
    Returns:
        Validated report
    """
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assessment returned null"
        )
    
    if report.get("status") == "NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment data available for this flight"
        )
    
    # Validate structure
    required_fields = ["flight_id", "status", "summary"]
    missing_fields = [f for f in required_fields if f not in report]
    
    if missing_fields:
        logger.warning(f"Assessment missing fields: {missing_fields}")
        # Don't fail, but log warning
    
    return report


def extract_flight_id_from_message(message: str) -> Optional[str]:
    """
    Extract flight ID from natural language message.
    
    Returns:
        Flight ID if found, None otherwise
    """
    # Common airline prefixes + numeric patterns
    # Looks for patterns like 6E123, AI1234, AA123, etc.
    pattern = r'\b([A-Z]{2})\s*(\d{3,4})\b'
    matches = re.findall(pattern, message.upper())
    
    if matches:
        prefix, number = matches[0]
        return f"{prefix}{number}"
    
    return None


# ---------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------
@app.get("/")
def root():
    return {
        "status": "Crew Lead Agent API is running",
        "service": "crew-lead-agent",
    }


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# Flight assessment endpoint
# ---------------------------------------------------------
@app.post("/assess/{flight_id}")
def assess_flight(flight_id: str):
    """
    Run the deterministic crew disruption assessment
    and recovery recommendation for a flight.
    
    Args:
        flight_id: Unique flight identifier (e.g., 6E123)
    
    Returns:
        Structured assessment with recommendations
    
    Raises:
        400: Invalid flight ID format
        404: Flight not found
        500: Internal server error
    """
    try:
        # Validate flight ID
        flight_id = validate_flight_id(flight_id)
        
        logger.info(f"Assessing flight {flight_id}")
        
        # Generate assessment
        report = build_crew_lead_report(flight_id)
        
        # Validate response structure
        report = validate_assessment_response(report)
        
        return {
            "flight_id": flight_id,
            "assessment": report,
            "decision_authority": "CREW_LEAD",
            "execution_performed": False,
        }
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error assessing flight {flight_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate assessment: {str(e)}"
        )


# ---------------------------------------------------------
# Natural-language Crew Lead Agent endpoint
# ---------------------------------------------------------
@app.post("/ask")
def ask_agent(request: CrewLeadRequest):
    """
    Send a natural-language request to the Crew Lead Agent.
    
    Args:
        request: CrewLeadRequest with message field
    
    Returns:
        Agent response (either structured assessment or text)
    
    Raises:
        400: Invalid or empty message
        422: Request validation failed
        500: Internal server error
    """
    try:
        message = request.message
        if not message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty",
            )
        logger.info(f"Processing agent request: {message[:100]}")
        
        # Try to extract flight ID from message
        flight_id = extract_flight_id_from_message(message)
        
        # If message contains assessment keywords and we found a flight ID,
        # use the deterministic assessment endpoint
        lowered = message.lower()
        assessment_keywords = ["assess", "disruption", "assessment", "status", "crew"]
        has_assessment_keyword = any(keyword in lowered for keyword in assessment_keywords)
        
        if flight_id and has_assessment_keyword:
            logger.info(f"Routing to assessment endpoint for flight {flight_id}")
            try:
                report = build_crew_lead_report(flight_id)
                report = validate_assessment_response(report)
                
                return {
                    "response": report,
                    "flight_id": flight_id,
                    "decision_authority": "CREW_LEAD",
                    "execution_performed": False,
                }
            except HTTPException as he:
                # If flight not found, fall through to agent
                logger.info(f"Flight {flight_id} not found, using agent instead")
        
        # Fall through to agent for general inquiries.
        # The deterministic API remains usable when optional LLM packages or
        # credentials are not installed.
        logger.info("Routing to LangGraph agent")
        try:
            runtime_agent = _load_optional_agent()
            if runtime_agent is None:
                return {
                    "response": (
                        "The LLM agent is not configured in this environment. "
                        "Use /assess/{flight_id} or include a valid flight ID "
                        "for deterministic crew assessment."
                    ),
                    "agent": "crew_lead_agent",
                    "agent_available": False,
                }

            result = runtime_agent.invoke({
                "messages": [
                    {"role": "user", "content": message}
                ]
            })
            
            if not result or "messages" not in result or not result["messages"]:
                raise ValueError("Agent returned empty response")
            
            final_message = result["messages"][-1].content
            
            if not final_message:
                raise ValueError("Agent response is empty")
            
            return {
                "response": final_message,
                "agent": "crew_lead_agent",
            }
        
        except Exception as agent_error:
            logger.error(f"Agent error: {str(agent_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent processing failed: {str(agent_error)}"
            )
    
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.error(f"Unexpected error in ask_agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request processing failed: {str(e)}"
        )


# ---------------------------------------------------------
# React UI data endpoints
# ---------------------------------------------------------
@app.get("/ui/flights")
def ui_flights():
    """Return CSV-backed flight data in the React console's shape."""

    return build_ui_flights()


@app.get("/ui/crew")
def ui_crew():
    """Return CSV-backed crew data with derived duty and risk fields."""

    return build_ui_crew()


@app.get("/ui/disruptions")
def ui_disruptions():
    """Return disruptions derived from the current flight and crew data."""

    return build_ui_disruptions()


@app.get("/ui/issues")
def ui_issues():
    """Return operational issues derived from the deterministic rules."""

    return build_ui_issues()


@app.get("/ui/recommendations")
def ui_recommendations():
    """Return current decision-support recommendations for disrupted flights."""

    return build_ui_recommendations()


@app.get("/ui/availability-snapshot")
def ui_availability_snapshot():
    return build_ui_snapshot()


@app.get("/ui/activity")
def ui_activity():
    """Return a current, non-persisted deterministic workflow snapshot."""

    return build_ui_activity()


@app.post("/ui/analyze")
def ui_analyze(request: UIAnalysisRequest):
    """Run a structured analysis for the React AI Crew Lead screen."""

    try:
        return build_ui_analysis(request.query)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("UI analysis failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate UI analysis.",
        )


# ---------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    logger.error(f"Validation error: {str(exc)}")
    return {
        "error": "Validation Error",
        "detail": str(exc),
        "status_code": 400
    }

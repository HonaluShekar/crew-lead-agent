from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import logging
import re
from typing import Optional

from src.crew_lead.agent import agent
from src.crew_lead.workflow import analyze_disruption, build_crew_lead_report


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
    def message_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message is too long (max 10000 characters)")
        return v.strip()


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
        
        # Fall through to agent for general inquiries
        logger.info("Routing to LangGraph agent")
        try:
            result = agent.invoke({
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
import requests
import streamlit as st
import json
import logging
from typing import Optional, Dict, Any


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BACKEND_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 60


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def validate_response_structure(assessment: Dict[str, Any]) -> bool:
    """Validate that assessment has required structure."""
    required_fields = ["flight_id", "status", "summary"]
    for field in required_fields:
        if field not in assessment:
            logger.warning(f"Assessment missing field: {field}")
            return False
    return True


def safe_get(obj: dict, key: str, default: Any = None) -> Any:
    """Safely get value from dict with fallback."""
    try:
        return obj.get(key, default) if isinstance(obj, dict) else default
    except Exception as e:
        logger.error(f"Error accessing {key}: {e}")
        return default


def format_duration(minutes: int) -> str:
    """Format minutes as human-readable duration."""
    if not isinstance(minutes, int):
        return "Unknown"
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="Crew Lead Agent",
    page_icon="✈️",
    layout="wide",
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("✈️ Crew Lead Agent")
st.caption(
    "Airline crew disruption decision-support system"
)

st.divider()


# ---------------------------------------------------------
# Flight assessment
# ---------------------------------------------------------

st.subheader("Flight Assessment")

flight_id = st.text_input(
    "Enter Flight ID",
    value="6E123",
    placeholder="Example: 6E123",
)

assess_button = st.button(
    "Assess Flight",
    type="primary",
)

# ---------------------------------------------------------
# Assessment request
# ---------------------------------------------------------

if assess_button:

    # Validate input
    if not flight_id or not flight_id.strip():
        st.warning("⚠️ Please enter a flight ID.")
        st.stop()

    flight_id = flight_id.strip().upper()
    
    # Validate flight ID format (basic check)
    if len(flight_id) < 3 or len(flight_id) > 10:
        st.error("❌ Invalid flight ID format. Expected format: 6E123")
        st.stop()

    with st.spinner(f"🔄 Assessing flight {flight_id}..."):

        try:

            response = requests.post(
                f"{BACKEND_URL}/assess/{flight_id}",
                timeout=REQUEST_TIMEOUT,
            )

            # -------------------------------------------------
            # Successful assessment
            # -------------------------------------------------

            if response.status_code == 200:

                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid response format from backend: {e}")
                    st.stop()

                assessment = data.get("assessment", {})
                
                # Validate response structure
                if not isinstance(assessment, dict):
                    st.error("❌ Backend returned invalid assessment structure")
                    st.stop()
                
                if not validate_response_structure(assessment):
                    st.warning("⚠️ Assessment may be incomplete")

                st.success(f"✅ Assessment completed for {flight_id}")

                # Display summary with fallback values
                summary = safe_get(assessment, "summary", {})
                if summary:
                    st.subheader("Flight Summary")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Route", safe_get(summary, "route", "N/A"))
                    with col2:
                        delay = safe_get(summary, "delay_minutes", 0)
                        st.metric("Delay", format_duration(delay))
                    with col3:
                        st.metric("Status", safe_get(assessment, "status", "N/A"))
                    with col4:
                        st.metric("Eligible Candidates", safe_get(summary, "eligible_candidate_count", 0))
                else:
                    st.warning("⚠️ Flight summary not available")

                # Display key findings
                st.subheader("Key Findings")
                key_findings = safe_get(assessment, "key_findings", [])
                if isinstance(key_findings, list) and key_findings:
                    for finding in key_findings:
                        if isinstance(finding, str):
                            st.write(f"• {finding}")
                elif not key_findings:
                    st.info("ℹ️ No key findings available.")
                else:
                    st.warning("⚠️ Key findings format invalid")

                # Display recommended action
                st.subheader("Recommended Action")
                recommended = safe_get(assessment, "recommended_action", {})
                if isinstance(recommended, dict) and recommended:
                    crew_id = safe_get(recommended, "crew_id", "No Crew")
                    name = safe_get(recommended, "name", crew_id)
                    message = safe_get(recommended, "message", "No recommendation available")
                    status = safe_get(recommended, "status", "UNKNOWN")
                    
                    st.markdown(f"**{name}** (ID: {crew_id})")
                    st.write(message)
                    st.caption(f"Status: {status}")
                elif not recommended:
                    st.info("ℹ️ No recommended action available.")
                else:
                    st.warning("⚠️ Recommended action format invalid")

                # Display alternative candidates
                st.subheader("Alternative Candidates by Role")
                alternatives = safe_get(assessment, "alternatives_by_role", {})
                if isinstance(alternatives, dict) and alternatives:
                    for role, candidates in alternatives.items():
                        st.markdown(f"### {role}")
                        if not candidates:
                            st.warning("❌ No eligible candidates found for this role.")
                            continue
                        
                        if not isinstance(candidates, list):
                            st.warning(f"⚠️ Invalid candidates format for {role}")
                            continue
                        
                        for candidate in candidates:
                            if not isinstance(candidate, dict):
                                continue
                            with st.container(border=True):
                                name = safe_get(candidate, "name", safe_get(candidate, "crew_id", "Unknown"))
                                st.write(f"**{name}**")
                                st.write(f"Crew ID: {safe_get(candidate, 'crew_id', 'N/A')}")
                                st.write(f"Role: {safe_get(candidate, 'role', 'N/A')}")
                                st.write(f"Status: {safe_get(candidate, 'recommendation_status', safe_get(candidate, 'status', 'N/A'))}")
                                st.write(f"Location: {safe_get(candidate, 'location_status', 'N/A')}")
                else:
                    st.info("ℹ️ No alternative candidates available.")

                st.divider()
                st.subheader("Crew Lead Note")
                note = safe_get(assessment, "crew_lead_note", "Decision support only.")
                st.info(note)

                st.divider()
                st.info(
                    "**Decision Authority:** Crew Lead\n\n"
                    "No crew assignment or operational change has been executed."
                )

            # -------------------------------------------------
            # HTTP errors
            # -------------------------------------------------

            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = safe_get(error_data, "detail", "Invalid request format")
                except:
                    error_message = "Invalid flight ID format"
                st.error(f"❌ Invalid Request: {error_message}")

            elif response.status_code == 404:
                st.error(f"❌ Flight Not Found: No data available for flight {flight_id}")
                st.info("Please verify the flight ID and try again. Example: 6E123")

            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    error_message = safe_get(error_data, "detail", "Internal server error")
                except:
                    error_message = "Internal server error"
                st.error(f"❌ Server Error: {error_message}")
                st.info("The backend encountered an error. Please try again later.")

            elif response.status_code == 422:
                st.error("❌ Validation Error: Request does not match expected format")

            else:
                st.error(f"❌ Backend Error (HTTP {response.status_code})")
                try:
                    error_data = response.json()
                    st.write(error_data)
                except:
                    st.write(response.text)

        # -------------------------------------------------
        # Connection error
        # -------------------------------------------------

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            st.error("❌ Connection Failed: Could not reach the backend")
            st.info(
                "Make sure the Crew Lead Agent backend is running:\n\n"
                "`python api.py`\n\n"
                "Backend URL: http://127.0.0.1:8000"
            )

        # -------------------------------------------------
        # Timeout
        # -------------------------------------------------

        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            st.error(f"❌ Timeout: Backend did not respond within {REQUEST_TIMEOUT} seconds")
            st.info("The backend may be processing a complex request. Please try again.")

        # -------------------------------------------------
        # Request error
        # -------------------------------------------------
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            st.error(f"❌ Request Error: {str(e)}")

        # -------------------------------------------------
        # Other errors
        # -------------------------------------------------

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            st.error(f"❌ Unexpected Error: {str(e)}")
            st.info("Please check the logs and try again.")
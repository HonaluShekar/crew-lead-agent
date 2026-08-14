"""
Comprehensive end-to-end test suite for Crew Lead Agent.

Tests cover:
- Valid flight scenarios
- Invalid/missing data handling
- Duty time edge cases
- Recovery options
- Downstream impact
- Error conditions
"""

from src.crew_lead.agent import agent
from datetime import datetime


def run_test(name, query, verbose=True):
    """Execute a test scenario and return results."""
    print("\n" + "=" * 80)
    print(f"TEST: {name}")
    print("=" * 80)

    try:
        result = agent.invoke({
            "messages": [
                ("user", query)
            ]
        })

        response = result["messages"][-1].content
        if verbose:
            print(response)
        else:
            print(response[:500] + "..." if len(response) > 500 else response)
        
        return {
            "status": "PASSED",
            "output": response
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            "status": "FAILED",
            "error": str(e)
        }


def run_workflow_test(name, tests):
    """Run a series of related tests."""
    print(f"\n\n{'#' * 80}")
    print(f"# WORKFLOW: {name}")
    print(f"{'#' * 80}")
    results = []
    for test_name, query in tests:
        result = run_test(test_name, query, verbose=True)
        results.append((test_name, result))
    return results


# ============================================================
# WORKFLOW 1: BASIC FLIGHT ASSESSMENT
# ============================================================

workflow_1_tests = [
    ("Valid Delayed Flight - Complete Assessment",
     """
     Perform a complete crew disruption assessment for flight 6E123.
     This flight is delayed. Identify the crew risks, replacement options,
     positioning requirements, conflicts, downstream impact, and recommended
     recovery actions.
     """),
    
    ("Flight Status Query",
     """
     What is the current status of flight 6E123?
     Who is assigned to it?
     """),
]

results_1 = run_workflow_test("BASIC FLIGHT ASSESSMENT", workflow_1_tests)


# ============================================================
# WORKFLOW 2: INVALID DATA HANDLING
# ============================================================

workflow_2_tests = [
    ("Non-existent Flight",
     """
     Perform a complete disruption assessment for flight INVALID999.
     """),
    
    ("Empty Flight ID",
     """
     Perform a complete disruption assessment for flight .
     """),
]

results_2 = run_workflow_test("INVALID DATA HANDLING", workflow_2_tests)


# ============================================================
# WORKFLOW 3: RECOVERY OPTIONS
# ============================================================

workflow_3_tests = [
    ("Find Replacement Crew for Captain",
     """
     For flight 6E123, what replacement options are available for the Captain?
     Show clean options, positioning-required options, and any conflicts.
     """),
    
    ("Find Replacement Crew for All Roles",
     """
     For flight 6E123, identify replacement options for Captain, First Officer,
     and Cabin Crew. Clearly separate: clean options, positioning-required,
     conflicts, and roles with no candidates.
     """),
    
    ("Evaluate Specific Candidate",
     """
     Can crew member C1842 (Rohan Mehta) be assigned to flight 6E123 as Captain?
     Check availability, qualification, duty limits, and conflicts.
     """),
]

results_3 = run_workflow_test("RECOVERY OPTIONS", workflow_3_tests)


# ============================================================
# WORKFLOW 4: DOWNSTREAM IMPACT
# ============================================================

workflow_4_tests = [
    ("Downstream Flight Impact",
     """
     If we reassign crew from flight 6E123 to a recovery flight,
     what downstream flights could be affected?
     List the downstream flights and explain the impact.
     """),
]

results_4 = run_workflow_test("DOWNSTREAM IMPACT", workflow_4_tests)


# ============================================================
# WORKFLOW 5: DUTY TIME EDGE CASES
# ============================================================

workflow_5_tests = [
    ("Duty Risk Assessment",
     """
     For flight 6E123, check the duty-time status of every assigned crew member.
     Report elapsed duty, remaining hours, and risk level for each.
     Is anyone approaching the duty limit?
     """),
]

results_5 = run_workflow_test("DUTY TIME EDGE CASES", workflow_5_tests)


# ============================================================
# WORKFLOW 6: OTHER DELAYED FLIGHTS
# ============================================================

workflow_6_tests = [
    ("Assessment of Flight 6E456",
     """
     Perform a complete crew disruption assessment for flight 6E456.
     """),
    
    ("Assessment of Flight 6E789",
     """
     Perform a complete crew disruption assessment for flight 6E789.
     What is its status? Are there any crew-related issues?
     """),
]

results_6 = run_workflow_test("OTHER DELAYED FLIGHTS", workflow_6_tests)


# ============================================================
# SUMMARY
# ============================================================

print("\n\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

all_results = results_1 + results_2 + results_3 + results_4 + results_5 + results_6
passed = sum(1 for _, r in all_results if r["status"] == "PASSED")
failed = sum(1 for _, r in all_results if r["status"] == "FAILED")

print(f"\nTotal Tests: {len(all_results)}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")

if failed > 0:
    print("\nFailed Tests:")
    for test_name, result in all_results:
        if result["status"] == "FAILED":
            print(f"  - {test_name}: {result['error']}")
else:
    print("\n🎉 All tests passed!")

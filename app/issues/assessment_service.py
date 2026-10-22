from datetime import datetime, timezone
from app.utils.datetime_utils import ensure_utc
from app.extensions import db
from app.models import Issue, LLMResponse
from app.issues.enums import IssueStatus, PriorityLevel
from app.priority.priority_engine import determine_priority_path, calculate_from_reference
from app.priority.llm_assessment import assess_issue_with_llm



def assess_issue(issue: Issue) -> Issue:
    """
    Assess a admin verified issue either a strong referece
    or LLM assessment path
    """

    assessment_path = determine_priority_path(description=issue.description)

    # Path 1 - Strong reference available - calculate directly from reference
    if assessment_path["path"] == "reference":
        result = calculate_from_reference(reference=assessment_path["reference"])

        issue.safety_score = result["safety_score"]
        issue.impact_score = result["impact_score"]
        issue.urgency_score = result["urgency_score"]
        issue.priority_score = result["priority_score"]
        issue.priority_level = PriorityLevel(result["priority_level"])

        issue.status = IssueStatus.IN_PROGRESS
        issue.aging_score = 0.0
        issue.aging_updated_at = ensure_utc(datetime.now(timezone.utc))

    # Path 2 - Moderate or weak reference - use LLM
    else:
        references = assessment_path["references"]
        result = assess_issue_with_llm(description=issue.description, references=references or None)

        # Usually None but if the issue was yet to be added to reference set, can use this
        response = issue.llm_response

        if response is None:
            response = LLMResponse(issue=issue)    # Due to the relationship between Issue and LLMResponse in models
            db.session.add(response)

        elif response.finalized:
            raise ValueError("A finalized assessement cannot be reassessed")

        # Preserve description and scope to issue table
        response.description = issue.description
        response.scope = issue.location_scope

        # save factor ranges
        response.safety_min, response.safety_max = (result["safety_score_range"])
        response.impact_min, response.impact_max = (result["impact_score_range"])
        response.urgency_min, response.urgency_max = (result["urgency_score_range"])

        # save calculated midpoints and overalll priority score and level
        response.safety_score = result["safety_score"]
        response.impact_score = result["impact_score"]
        response.urgency_score = result["urgency_score"]
        response.priority_score = result["priority_score"]
        response.priority_level = PriorityLevel(result["priority_level"])

        response.finalized = False
        response.added_to_vector_db = False

        issue.status = IssueStatus.PENDING_APPROVAL
        issue.aging_updated_at = None

    return issue



def approve_assessment(issue: Issue) -> Issue:
    """
    Finalize an llm assessment (admin approval) and copy its
    approved scores to issue table
    """

    response = issue.llm_response

    if response is None:
        raise ValueError("No LLM assessment exists for this issue")

    if response.finalized:
        raise ValueError("This assessment has already been finalized")

    if issue.status != IssueStatus.PENDING_APPROVAL:
        raise ValueError("This issue is not awaiting assessment approval")

    now = ensure_utc(datetime.now(timezone.utc))

    # Mark admin approved assessment as finalized
    response.finalized = True

    # Copy approved scores to operational issue record
    issue.safety_score = response.safety_score
    issue.impact_score = response.impact_score
    issue.urgency_score = response.urgency_score
    issue.priority_score = response.priority_score
    issue.priority_level = response.priority_level

    # Start issue's active life-cycle and aging clock
    issue.status = IssueStatus.IN_PROGRESS
    issue.aging_score = 0.0
    issue.aging_updated_at = now

    return issue
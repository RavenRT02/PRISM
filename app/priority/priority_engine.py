from app.issues.enums import IssueStatus, PriorityLevel
from datetime import datetime, timezone
from app.similarity_search.reference_store import find_similar_references
from app.utils.datetime_utils import ensure_utc
from app.priority.priority_score_cal import find_midpoint, calculate_priority_score as calculate_initial_priority_score
from app.models import Issue



IDEAL_THRESHOLD = 0.70
MINIMAL_THRESHOLD = 0.55


def determine_priority_path(description: str) -> dict:
    """
    Retrieve similar references and decide how issues
    should be assessed. Returns dict describing selected path
    """

    references = find_similar_references(description=description, n_results=3)

    # No reference available : use llm without examples (only possible if vector db is empty)
    if not references:
        return {
            "path" : "llm_without_examples",
            "references" : []
        }

    # ChromaDB returns references ordered by similarity
    best_reference = references[0]
    best_similarity = best_reference["similarity"]

    # Strong match : use best reference for scoring directly
    # reference - top similarity reference, references - top 3 references
    if best_similarity >= IDEAL_THRESHOLD:
        return {
            "path" : "reference",
            "reference" : best_reference,
            "references" : references
        }

    # Moderate match : use llm with examples
    if best_similarity >= MINIMAL_THRESHOLD:

        examples = [reference 
            for reference in references
            if references["similarity"] >= MINIMAL_THRESHOLD]

        return {
            "path" : "llm_with_examples",
            "reference" : examples
        }

    # Weak match : use llm without reference examples
    return {
        "path" : "llm_without_examples",
        "references" : []
    }


# This is used when strong references are available for the issue, llm path does not use this
def calculate_from_reference(reference: dict) -> dict:
    """
    Calculate factor midpoints and initial priority score and tag
    from a reference's score range 
    """

    safety, impact, urgency = find_midpoint(
        reference["safety_score_range"], reference["impact_score_range"], reference["urgency_score_range"]
    )

    priority_score, priority_level = calculate_initial_priority_score(safety=safety, impact=impact, urgency=urgency)

    return {
        "safety_score" : safety,
        "impact_score" : impact,
        "urgency_score" : urgency,
        "priority_score" : priority_score,
        "priority_level" : priority_level
    }




def check_hold_expiry(issue : Issue) -> bool:

    if issue.status != IssueStatus.ON_HOLD:
        return False
    
    if not issue.hold_until:
        return False

    now = ensure_utc(datetime.now(timezone.utc))
    hold_until = ensure_utc(issue.hold_until)
    return now >= hold_until




def update_issue_priority(issue):

    pass



def update_aging(issue):

    if not issue.approved_at:
        return
    
    now = ensure_utc(datetime.now(timezone.utc))
    
    days_elapsed = (now - issue.approved_at).days

    # issue.aging_score = (days_elapsed // AGING_INCREMENT_DAYS) * AGING_SCORE_STEP




def clean_and_lemmatize(description):
    
    pass


def infer_urgency_score(cleaned_description):

    pass


def infer_impact_score(cleaned_description):

    pass


def auto_score_issue(issue):

    if not issue.description:
        issue.urgency_score = 0
        issue.impact_score = 0
        return issue

    cleaned_desc = clean_and_lemmatize(issue.description)

    issue.urgency_score = infer_urgency_score(cleaned_desc)
    issue.impact_score = infer_impact_score(cleaned_desc)

    return issue



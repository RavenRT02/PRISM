from app.issues.enums import IssueStatus
from datetime import datetime, timezone
from app.similarity_search.reference_store import find_similar_references
from app.utils.datetime_utils import ensure_utc
from app.priority.priority_score_cal import (
    find_midpoint, calculate_priority_score as calculate_initial_priority_score, assign_priority_level)
from app.models import Issue


# Similarity threshold
IDEAL_THRESHOLD = 0.70
MINIMAL_THRESHOLD = 0.55


# Aging constants
AGING_MAX_SCORE = 10.0
AGING_FIRST_TIER_CAP = 5
AGING_FIRST_TIER_RATE = 0.5
AGING_SECOND_TIER_RATE = 0.1
SECONDS_PER_DAY = 24 * 60 * 60


def determine_priority_path(description: str) -> dict:
    """
    Retrieve similar references and decide how issues
    should be assessed. Returns dict describing selected path.
    Choose reference scoring, LLM scoring with examples, or LLM alone.
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
            if reference["similarity"] >= MINIMAL_THRESHOLD]

        return {
            "path" : "llm_with_examples",
            "references" : examples
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




def check_hold_expiry(issue: Issue, now: datetime | None = None) -> bool:
    """Return whether an ON_HOLD issue's hold deadline has passed"""

    if issue.status != IssueStatus.ON_HOLD or not issue.hold_until:
        return False

    now = ensure_utc(now or datetime.now(timezone.utc))
    return now >= ensure_utc(issue.hold_until)



def calculate_aging_increment(current_score: float, elapsed_seconds: float) -> float:
    """
    Apply elapsed eligible time across the two aging tiers
    current_score - already added aging score, 
    elapsed_seconds - time spent since last aging calculation
    """

    if elapsed_seconds <= 0 or current_score >= AGING_MAX_SCORE:
        return 0.0

    remaining_days = elapsed_seconds / SECONDS_PER_DAY        
    increment = 0.0

    # Tier 1 - increase aging score by 0.5 per day (upto 5 points)
    if current_score < AGING_FIRST_TIER_CAP and remaining_days > 0:
        points_available = AGING_FIRST_TIER_CAP - current_score 
        days_needed = points_available / AGING_FIRST_TIER_RATE       # to reach 1st tier cap
        days_used = min(remaining_days, days_needed)                 # Days consumed by current tier
        tier_increment = days_used * AGING_FIRST_TIER_RATE
        increment += tier_increment
        current_score += tier_increment
        # helps with Tier 2 calculation in case aging is not calculated on a daily base and days since last aging accumulates
        remaining_days -= days_used             

    # Tier 2 - increase aging score bt 0.1 per day (6 - 10 points)
    if current_score < AGING_MAX_SCORE and remaining_days > 0:
        points_available = AGING_MAX_SCORE - current_score
        days_needed = points_available / AGING_SECOND_TIER_RATE
        days_used = min(remaining_days, days_needed)
        increment += days_used * AGING_SECOND_TIER_RATE

    return min(increment, AGING_MAX_SCORE)




def update_aging(issue: Issue, now: datetime | None = None) -> None:
    """Accumulate aging only for elapsed time spent in IN_PROGRESS"""

    # Issue status is not IN_PROGRESS -- do not do anything, end the function with empty return
    if issue.status != IssueStatus.IN_PROGRESS:
        return

    # current time
    now = ensure_utc(now or datetime.now(timezone.utc))

    # Starting or resuming an issue establishes the clock; it does not age the issue for time spent in another status.
    # When last aging update is not found (1st use) set it as current time (now) and end fucntion with empty return
    if not issue.aging_updated_at:
        issue.aging_updated_at = now
        return

    last_updated = ensure_utc(issue.aging_updated_at)
    elapsed_seconds = max((now - last_updated).total_seconds(), 0.0)  # .total_seconds() convert value to seconds

    # min((existing aging score + newly calculated additional aging score), Max aging score)
    issue.aging_score = min(
        (issue.aging_score or 0.0) + calculate_aging_increment(current_score=issue.aging_score or 0.0, elapsed_seconds=elapsed_seconds), 
        AGING_MAX_SCORE
        )

    issue.aging_updated_at = now




def update_issue_priority(issue: Issue, now: datetime | None = None) -> None:
    """Refresh aging, final priority score, and priority level in place"""

    # If any of the 3 factor scores is missing, do nothing and end the function with empty return
    if any(score is None for score in (issue.safety_score, issue.impact_score, issue.urgency_score)):
        return

    # update aging
    update_aging(issue=issue, now=now)

    base_score, _ = calculate_initial_priority_score(
        safety=issue.safety_score, impact=issue.impact_score, urgency=issue.urgency_score
    )

    issue.aging_score = min(max(issue.aging_score or 0.0, 0.0), AGING_MAX_SCORE)  # never exceeds max aging score
    final_score = min(base_score + issue.aging_score, 100)   # never exceeds 100
    issue.priority_score = round(final_score, 2)
    issue.priority_level = assign_priority_level(score=final_score)

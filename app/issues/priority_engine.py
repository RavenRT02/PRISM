from app.issues.enums import PriorityLevel, IssueStatus
from datetime import datetime, timezone
from app.utils.datetime_utils import ensure_utc

URGENCY_WEIGHT = 5
IMPACT_WEIGHT = 4
AGING_WEIGHT = 1

AGING_INCREMENT_DAYS = 3
AGING_SCORE_STEP = 2

PRIORITY_THRESHOLDS = [(PriorityLevel.CRITICAL, 80), (PriorityLevel.HIGH, 60), (PriorityLevel.MEDIUM, 40),]


def calculate_priority_score(issue):

    urgency = max(issue.urgency_score or 0, 0)
    impact = max(issue.impact_score or 0, 0)
    aging = max(issue.aging_score or 0, 0)

    return ( (urgency * URGENCY_WEIGHT) 
             + (impact * IMPACT_WEIGHT)
             + (aging * AGING_WEIGHT))


def assign_priority_level(score):

    for level, threshold in PRIORITY_THRESHOLDS:
        if score >= threshold:
            return level
    
    return PriorityLevel.LOW


def update_issue_priority(issue):

    update_aging(issue)

    score = calculate_priority_score(issue)

    issue.priority_score = score
    issue.priority_level = assign_priority_level(score)

    return issue



def update_aging(issue):

    if not issue.approved_at:
        return
    
    now = ensure_utc(datetime.now(timezone.utc))
    
    days_elapsed = (now - issue.approved_at).days

    issue.aging_score = (days_elapsed // AGING_INCREMENT_DAYS) * AGING_SCORE_STEP


def check_hold_expiry(issue):

    if issue.status != IssueStatus.ON_HOLD:
        return False
    
    if not issue.hold_until:
        return False

    now = ensure_utc(datetime.now(timezone.utc))
    hold_until = ensure_utc(issue.hold_until)
    return now >= hold_until


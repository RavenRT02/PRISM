from app.extensions import db
from app.models import IssueFollower, Issue, IssueStatusHistory
from app.issues.duplicate_detection import find_duplicate
from app.issues.enums import IssueStatus, LocationScope
from datetime import datetime, timezone
from app.priority.priority_engine import update_issue_priority, check_hold_expiry
from app.issues.assessment_service import assess_issue
from app.utils.datetime_utils import ensure_utc


def follow_issue(user_id, issue_id):

    existing = IssueFollower.query.filter_by(user_id = user_id, issue_id = issue_id).first()

    if existing:
        return existing

    follower = IssueFollower(user_id = user_id, issue_id = issue_id)
    db.session.add(follower)
    db.session.commit()

    return follower


def detect_duplicate_issue(candidate_issue):

    existing_issue = Issue.query.filter(Issue.building_id == candidate_issue.building_id,
                                        Issue.floor_id == candidate_issue.floor_id,
                                        Issue.room_id == candidate_issue.room_id,
                                        Issue.status.in_([IssueStatus.SUBMITTED, IssueStatus.IN_PROGRESS, IssueStatus.ON_HOLD])).all()
    
    duplicate_issue = find_duplicate(candidate_issue, existing_issue)

    return duplicate_issue


def create_issue(candidate_issue):

    candidate_issue.status = IssueStatus.SUBMITTED
    candidate_issue.location_scope = LocationScope.ROOM
    
    db.session.add(candidate_issue)
    db.session.commit()

    return candidate_issue


def verify_issue(issue, admin_user, title, category_id = None):

    issue.title = title

    if category_id:
        issue.category_id = category_id

    issue.verified_by = admin_user.id
    issue.verified_at = ensure_utc(datetime.now(timezone.utc))

    # Find assessment path and populate Issue or LLMResponse models accordingly
    assess_issue(issue=issue)

    return issue


def reject_issue(issue, admin_user, reason = None):

    issue.status = IssueStatus.REJECTED
    issue.verified_by = admin_user.id
    issue.verified_at = ensure_utc(datetime.now(timezone.utc))
    issue.review_notes = reason

    db.session.commit()

    return issue



def release_expired_holds():
    """Resume expired holds without counting time spent ON_HOLD as aging time"""

    held_issues = Issue.query.filter(Issue.status == IssueStatus.ON_HOLD).all()
    now = ensure_utc(datetime.now(timezone.utc))

    released = []

    for issue in held_issues:
        if not check_hold_expiry(issue=issue, now=now):
            continue

        # For issues whose hold time expires, update status and add continue aging
        old_status = issue.status
        issue.status = IssueStatus.IN_PROGRESS
        issue.hold_until = None
        issue.status_changed_at = now
        issue.aging_updated_at = now

        history = IssueStatusHistory(issue_id=issue.id, old_status=old_status, new_status=IssueStatus.IN_PROGRESS,
            changed_at=now, note="Automatically resumed after hold expired")

        db.session.add(history)
        released.append(issue)

    if released:
        db.session.commit()

    return len(released)


def log_status_change(issue, old_status, new_status, user_id=None, note=None):

    history = IssueStatusHistory(issue_id=issue.id, old_status=old_status if old_status else None,
                                 new_status=new_status, changed_by=user_id, note=note)

    db.session.add(history)
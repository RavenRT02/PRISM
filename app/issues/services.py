from app.extensions import db
from app.models import IssueFollower, Issue
from app.issues.duplicate_detection import find_duplicate
from app.issues.enums import IssueStatus
from datetime import datetime, timezone
from app.issues.priority_engine import update_issue_priority
from app.utils.datetime_utils import ensure_utc
from app.issues.priority_engine import check_hold_expiry


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
                                        Issue.status.in_([IssueStatus.SUBMITTED, IssueStatus.UNDER_REVIEW,
                                                         IssueStatus.APPROVED, IssueStatus.PRIORITIZED, IssueStatus.ON_HOLD])).all()
    
    duplicate_issue = find_duplicate(candidate_issue, existing_issue)

    return duplicate_issue


def create_issue(candidate_issue):

    candidate_issue.status = IssueStatus.SUBMITTED
    db.session.add(candidate_issue)
    db.session.commit()

    return candidate_issue


def verify_issue(issue, admin_user, title, category_id = None):

    issue.title = title

    if category_id:
        issue.category_id = category_id

    issue.verified_by = admin_user.id
    issue.verified_at = ensure_utc(datetime.now(timezone.utc))
    issue.status = IssueStatus.PRIORITIZED

    update_issue_priority(issue)
    db.session.commit()

    return issue


def reject_issue(issue, admin_user, reason = None):

    issue.status = IssueStatus.REJECTED
    issue.verified_by = admin_user.id
    issue.verified_at = ensure_utc(datetime.now(timezone.utc))
    issue.review_notes = reason

    db.session.commit()

    return issue


def release_expired_holds():

    held_issues = Issue.query.filter(Issue.status == IssueStatus.ON_HOLD).all()
    now = ensure_utc(datetime.now(timezone.utc))

    released = []

    for issue in held_issues:

        if issue.hold_until:

            hold_until = ensure_utc(datetime.now(timezone.utc))

            if now >= hold_until:

                issue.status == IssueStatus.PRIORITIZED
                issue.hold_until = None
                issue.status_changed_at = now
                released.append(issue)
    
    if released:
        db.session.commit()

    return len(released)
from app.extensions import db
from app.models import IssueFollower, Issue
from app.issues.duplicate_detection import find_duplicate
from app.issues.enums import IssueStatus


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
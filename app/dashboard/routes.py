from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.issues.services import release_expired_holds
from app.models import Issue, IssueCategory
from app.issues.enums import IssueStatus
from sqlalchemy import func
from app.extensions import db



dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():

    release_expired_holds()

    issues = Issue.query.filter(Issue.status == IssueStatus.PRIORITIZED,
        Issue.priority_override == False).order_by(Issue.priority_score.desc()).all()
    
    verification_queue = Issue.query.filter(Issue.status == IssueStatus.SUBMITTED).order_by(Issue.created_at.asc()).all()

    prioritized = Issue.query.filter(Issue.priority_override == True).all()

    on_hold = Issue.query.filter(Issue.status == IssueStatus.ON_HOLD).all()

    resolved = Issue.query.filter(Issue.status == IssueStatus.RESOLVED).all()

    closed = Issue.query.filter(Issue.status == IssueStatus.CLOSED).all()

    category_stats = db.session.query(IssueCategory.name, func.count(Issue.id)).join(Issue).group_by(IssueCategory.name).all()

    category_labels = [c[0] for c in category_stats]
    category_counts = [c[1] for c in category_stats]

    return render_template("admin_dashboard.html", issues=issues, prioritized=prioritized,
                            on_hold=on_hold, resolved=resolved, closed=closed, verification_queue = verification_queue,
                            issues_count = len(issues), prioritized_count = len(prioritized), 
                            on_hold_count = len(on_hold), resolved_count = len(resolved), closed_count = len(closed),
                            category_labels = category_labels, category_counts = category_counts)



@dashboard_bp.route("/user/dashboard")
@login_required
def user_dashboard():

    user_issues = Issue.query.filter(Issue.created_by == current_user.id).all()

    return render_template("user_dashboard.html", issues=user_issues)
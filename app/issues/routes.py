from flask import Blueprint, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Issue
from app.utils.toxicity import contains_toxicity
from app.issues.enums import IssueStatus, IssueType
from app.issues.services import detect_duplicate_issue, follow_issue, create_issue


issues_bp = Blueprint("issues", __name__, url_prefix = "/issues")


@issues_bp.route("/submit", methods = ['POST'])
@login_required
def submit_issue():
    
    description = request.form.get("description")
    building_id = request.form.get("building_id")
    floor_id = request.form.get("floor_id")
    room_id = request.form.get("room_id")
    category_id = request.form.get("category_id")
    issue_type = request.form.get("issue_type")

    if not description:
        flash("Description required", "error")
        return redirect(url_for("user.dashboard"))
    
    if contains_toxicity(description):
        flash("Issue  description contains inappropriate language", "error")
        return redirect(url_for("user.dashboard"))
    
    candidate_issue = Issue(description = description, building_id = building_id, floor_id = floor_id,
                            room_id = room_id, category_id = category_id, issue_type = issue_type,
                            created_by = current_user.id, status = IssueStatus.SUBMITTED)
    
    
    duplicate_issue = detect_duplicate_issue(candidate_issue)

    if duplicate_issue:
        flash("Similar issue already exists, would you like to track instead?", "warning")
        return redirect(url_for("issues.track_duplicate", issue_id = duplicate_issue.id))
        
    create_issue(candidate_issue)
    flash("Issue submitted successfully", "success")
    return redirect(url_for("user.dashboard"))



@issues_bp.route("/track/<int:issue_id>")
@login_required
def track_duplicate(issue_id):

    follow_issue(current_user.id, issue_id)
    flash("You are now tracking this issue", "success")

    return redirect(url_for("user.dashboard"))

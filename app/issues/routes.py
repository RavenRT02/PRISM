from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Issue, Building, Floor, Room, IssueCategory
from app.utils.toxicity import contains_toxicity
from app.issues.enums import IssueStatus, IssueType
from app.issues.services import detect_duplicate_issue, follow_issue, create_issue, verify_issue, reject_issue, log_status_change
from app.utils.decorators import admin_required
from datetime import datetime, timezone, timedelta
from app.utils.datetime_utils import ensure_utc
import os 
from werkzeug.utils import secure_filename


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
    image = request.files.get("image")

    image_path = None

    if not description or len(description.strip()) < 10:
        flash("Description must be at least 10 characters long", "warning")
        return redirect(request.referrer or url_for("dashboard.user_dashboard"))
    
    if contains_toxicity(description):
        flash("Issue description contains inappropriate language", "error")
        return redirect(request.referrer or url_for("dashboard.user_dashboard"))
    
    if image and image.filename:

        filename = secure_filename(image.filename)

        filepath = os.path.join("uploads", filename)

        image.save(os.path.join("app/static", filepath))

        image_path = filepath
    
    candidate_issue = Issue(description = description, building_id = building_id, floor_id = floor_id,
                            room_id = room_id, category_id = category_id, issue_type = issue_type,
                            created_by = current_user.id, status = IssueStatus.SUBMITTED, image_path = image_path)
    
    
    duplicate_issue = detect_duplicate_issue(candidate_issue)

    if duplicate_issue:
        flash("Similar issue already exists, would you like to track instead?", "warning")
        return render_template("issues/duplicate_found.html", duplicate_issue = duplicate_issue, candidate_issue = candidate_issue)
        
    create_issue(candidate_issue)
    flash("Issue submitted successfully", "success")
    return redirect(url_for("dashboard.user_dashboard"))



@issues_bp.route("/track/<int:issue_id>")
@login_required
def track_duplicate(issue_id):

    follow_issue(current_user.id, issue_id)
    flash("You are now tracking this issue", "success")

    return redirect(url_for("dashboard.user_dashboard"))



@issues_bp.route("/delete/<int:issue_id>", methods=['POST'])
@login_required
def delete_issue_route(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    
    if issue.created_by != current_user.id:
        flash("You are not authorized to delete this issue.", "error")
        return redirect(url_for("dashboard.user_dashboard"))
        
    if issue.status.name not in ["RESOLVED", "CLOSED", "REJECTED"]:
        flash("Only resolved, closed, or rejected issues can be deleted.", "error")
        return redirect(url_for("dashboard.user_dashboard"))
        
    db.session.delete(issue)
    db.session.commit()
    flash("Issue permanently deleted.", "success")
    return redirect(url_for("dashboard.user_dashboard"))



@issues_bp.route("/verify/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def verify_issue_route(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    title = request.form.get("title")
    category_id = request.form.get("category_id")

    if not title:
        flash("Issue title is required", "error")
        return redirect(url_for("issues.issue_details", issue_id = issue.id))
    
    old_status = issue.status
    
    verify_issue(issue, current_user, title, category_id)
    flash("Issue verified and prioritized successfully")

    log_status_change(issue, old_status, issue.status, current_user.id, "Issue verified by admin")

    return redirect(url_for("dashboard.admin_dashboard"))



@issues_bp.route("/reject/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def reject_issue_route(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    reason = request.form.get("reason")

    old_status = issue.status

    reject_issue(issue, current_user, reason)
    flash("Issue rejected successfully", "info")

    log_status_change(issue, old_status, issue.status, current_user.id, "Issue verified by admin")

    return redirect(url_for("dashboard.admin_dashboard"))



@issues_bp.route("/<int:issue_id>")
@login_required
def issue_details(issue_id):

    issue = Issue.query.get_or_404(issue_id)

    return render_template("issues/issue_detail.html", issue = issue)



@issues_bp.route("/prioritize/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def prioritize_issue(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    issue.priority_override = True

    db.session.commit()
    flash("Issue manually prioritized", "success")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))



@issues_bp.route("/unprioritize/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def unprioritize_issue(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    issue.priority_override = False

    db.session.commit()
    flash("Manual prioritization removed", "info")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))



@issues_bp.route("/hold/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def hold_issue(issue_id):


    issue = Issue.query.get_or_404(issue_id)
    old_status = issue.status
    HOLD_DURATION_DAYS = 3
    issue.status = IssueStatus.ON_HOLD
    issue.hold_until = ensure_utc(datetime.now(timezone.utc)) + timedelta(days=HOLD_DURATION_DAYS)
    issue.status_changed_at = ensure_utc(datetime.now(timezone.utc))

    log_status_change(issue, old_status, issue.status, current_user.id, "Issue verified by admin")

    db.session.commit()
    flash("Issue moved to On Hold", "warning")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))



@issues_bp.route("/resolve/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def resolve_issue(issue_id):


    issue = Issue.query.get_or_404(issue_id)
    old_status = issue.status
    issue.status = IssueStatus.RESOLVED
    issue.status_changed_at = ensure_utc(datetime.now(timezone.utc))

    log_status_change(issue, old_status, issue.status, current_user.id, "Issue verified by admin")

    db.session.commit()
    flash("Issue marked as resolved", "success")

    return redirect(url_for("dashboard.admin_dashboard"))



@issues_bp.route("/close/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def close_issue(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    reason = request.form.get("reason")
    tracker_id = request.form.get("duplicate_id")
    old_status = issue.status

    issue.status = IssueStatus.CLOSED
    issue.status_changed_at = ensure_utc(datetime.now(timezone.utc))
    
    if reason:
        issue.review_notes = reason

    db.session.commit()
    
    # Core Logic: If admin links an active duplicate, secretly assign the ticket-creator to track it!
    if tracker_id and tracker_id.isdigit():
        target_issue = Issue.query.get(int(tracker_id))
        if target_issue:
            follow_issue(issue.created_by, target_issue.id)
            issue.review_notes = (issue.review_notes or "") + f" [System] Tracked to Issue #{target_issue.id} automatically."
            db.session.commit()

    flash("Issue marked as closed", "secondary")

    log_status_change(issue, old_status, issue.status, current_user.id, f"Issue administratively closed: {reason}" if reason else "Issue administratively closed")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))


@issues_bp.route("/rename/<int:issue_id>", methods=["POST"])
@login_required
@admin_required
def rename_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    new_title = request.form.get("title")

    if not new_title:
        flash("Title cannot be empty.", "error")
    else:
        issue.title = new_title
        db.session.commit()
        flash("Ticket title renamed successfully.", "success")

    return redirect(url_for("issues.issue_details", issue_id=issue.id))


@issues_bp.route("/resume/<int:issue_id>", methods=["POST"])
@login_required
@admin_required
def resume_issue(issue_id):
    issue = Issue.query.get_or_404(issue_id)
    
    if issue.status != IssueStatus.ON_HOLD:
        flash("Can only resume tickets that are currently on hold.", "warning")
        return redirect(url_for("issues.issue_details", issue_id=issue.id))

    old_status = issue.status
    issue.status = IssueStatus.PRIORITIZED
    issue.hold_until = None
    
    db.session.commit()
    flash("Ticket resumed to Active Pipeline.", "success")
    log_status_change(issue, old_status, issue.status, current_user.id, "Manually retrieved from On Hold.")
    
    return redirect(url_for("issues.issue_details", issue_id=issue.id))



@issues_bp.route("/raise", methods=["GET"])
@login_required
def raise_issue_form():

    buildings = Building.query.filter_by(is_active=True).all()

    categories = IssueCategory.query.filter_by(is_active=True).all()

    return render_template("issues/raise_issue.html", buildings=buildings, categories=categories)



@issues_bp.route("/floors/<int:building_id>")
@login_required
def get_floors(building_id):

    floors = Floor.query.filter_by(building_id=building_id, is_active=True).all()

    return jsonify([{"id": f.id, "number": f.number}for f in floors])



@issues_bp.route("/rooms/<int:floor_id>")
@login_required
def get_rooms(floor_id):

    rooms = Room.query.filter_by(floor_id=floor_id, is_active=True).all()

    return jsonify([{"id": r.id, "name": r.name}for r in rooms])
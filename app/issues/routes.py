from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Issue, Building, Floor, Room, IssueCategory, LLMResponse, LocationScope
from app.utils.toxicity import contains_toxicity
from app.issues.enums import IssueStatus, PriorityLevel, IssueType
from app.issues.services import detect_duplicate_issue, follow_issue, create_issue, verify_issue, reject_issue, log_status_change
from app.utils.decorators import admin_required
from datetime import datetime, timezone, timedelta
from app.utils.datetime_utils import ensure_utc
from app.priority.priority_engine import update_issue_priority
from app.priority.priority_score_cal import find_midpoint, calculate_priority_score
from app.issues.assessment_service import approve_assessment
from app.similarity_search.reference_store import ingest_approved_response
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

    scope_raw = request.form.get("location_scope", "ROOM")

    try:
        location_scope = LocationScope(scope_raw)
    except ValueError:
        flash("Please select a valid issue scope.", "error")
        return redirect(request.referrer or url_for("dashboard.user_dashboard"))

    building_id = request.form.get("building_id", type=int)
    floor_id = request.form.get("floor_id", type=int) or None
    room_id = request.form.get("room_id", type=int) or None

    if not building_id:
        flash("Please select a building.", "warning")
        return redirect(request.referrer or url_for("dashboard.user_dashboard"))

    if location_scope == LocationScope.BUILDING:
        floor_id = None
        room_id = None

    elif location_scope == LocationScope.FLOOR:
        room_id = None
        if not floor_id:
            flash("Please select a floor.", "warning")
            return redirect(request.referrer or url_for("dashboard.user_dashboard"))

    elif location_scope == LocationScope.ROOM:
        if not floor_id or not room_id:
            flash("Please select a floor and room.", "warning")
            return redirect(request.referrer or url_for("dashboard.user_dashboard"))
        

    building = db.session.get(Building, building_id)

    if building is None:
        flash("Invalid building selection.", "error")
        return redirect(request.referrer or url_for("dashboard.user_dashboard"))

    if floor_id is not None:
        floor = db.session.get(Floor, floor_id)

        if floor is None or floor.building_id != building_id:
            flash("The selected floor does not belong to that building.", "error")
            return redirect(request.referrer or url_for("dashboard.user_dashboard"))

    if room_id is not None:
        room = db.session.get(Room, room_id)

        if room is None or room.floor_id != floor_id:
            flash("The selected room does not belong to that floor.", "error")
            return redirect(request.referrer or url_for("dashboard.user_dashboard"))
            
    
    candidate_issue = Issue(description = description, location_scope=location_scope, building_id = building_id, 
                            floor_id = floor_id, room_id = room_id, category_id = category_id, issue_type = issue_type,
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

    try:
        verify_issue(issue, current_user, title, category_id)
        log_status_change(issue, old_status, issue.status, current_user.id, "Issue verified by admin")
        db.session.commit()

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to verify issue")
        flash("Unable to verify the issue. Please try again.", "error")
        return redirect(url_for("issues.issue_details", issue_id=issue.id))

    if issue.status == IssueStatus.PENDING_APPROVAL:
        flash("Issue assessed and submitted for admin approval", "success")

    elif issue.status == IssueStatus.IN_PROGRESS:
        flash("Issue verified and added to active queue", "success")

    return redirect(url_for("dashboard.admin_dashboard"))




@issues_bp.route("/pending-assessments")
@login_required
@admin_required
def pending_assessments():

    pending_issues = Issue.query.filter_by(status=IssueStatus.PENDING_APPROVAL).order_by(Issue.created_at.asc()).all()

    return render_template("issues/pending_assessments.html", pending_issues=pending_issues)


# Allows admin to approve llm response or save edits to range (saving does not approve)
@issues_bp.route("/review-assessment/<int:issue_id>", methods = ['GET', 'POST'])
@login_required
@admin_required
def review_assessment(issue_id):

    issue = Issue.query.get_or_404(issue_id)
    response = issue.llm_response

    # will not trigger if pipeline is system following pipeline properly, just a failsafe condition
    if issue.status != IssueStatus.PENDING_APPROVAL:
        flash(
            f"Issue status is {issue.status.name}, not PENDING_APPROVAL.",
            "warning",
        )
        return redirect(url_for("dashboard.admin_dashboard"))

    if response is None:
        flash("This issue has no linked LLM assessment record.", "error")
        return redirect(url_for("dashboard.admin_dashboard"))

    if response.finalized:
        flash("This assessment has already been finalized.", "warning")
        return redirect(url_for("dashboard.admin_dashboard"))

    if request.method == 'POST':
        try:
            # Read and validate the six editable range values
            ranges = {}

            for factor in ("safety", "impact", "urgency"):
                minimum = float(request.form.get(f'{factor}_min', ""))
                maximum = float(request.form.get(f'{factor}_max', ""))

                if not (0 <= minimum <= 100) and (0 <= maximum <= 100):
                    raise ValueError(f'{factor.title()} scores must be between 0 and 100')

                if minimum > maximum:
                    raise ValueError(f'{factor.title()} minimum cannot exceed its maximum')

                ranges[factor] = (minimum, maximum)

            # Store the edited ranges to llm response table
            response.safety_min, response.safety_max = ranges["safety"]
            response.impact_min, response.impact_max = ranges["impact"]
            response.urgency_min, response.urgency_max = ranges["urgency"]

            # Recalculate midpoints using existing scoring utilities
            safety, impact, urgency = find_midpoint(
                safety_range=list(ranges["safety"]), impact_range=list(ranges["impact"]), urgency_range=list(ranges["urgency"])
                )

            priority_score, priority_level = calculate_priority_score(safety=safety, impact=impact, urgency=urgency)

            response.safety_score = safety
            response.impact_score = impact
            response.urgency_score = urgency
            response.priority_score = priority_score
            response.priority_level = PriorityLevel(priority_level)

            action = request.form.get("action")

            if action == "approve":
                old_status = issue.status
                approve_assessment(issue=issue)

                log_status_change(issue, old_status, issue.status, current_user.id, "LLM assessment reviewed and approved by admin")

                # Commit approval
                db.session.commit()

                # Attempt ingestion to reference dataset

                try:
                    ingest_approved_response(response=response)
                    response.added_to_vector_db = True
                    db.session.commit()

                    flash("Assessment approved and added to reference dataset and active queue", "success")

                except:
                    db.session.rollback()
                    current_app.logger.exception("Assessment approved but ingestion failed for %s", issue.id)
                    flash("Assessment approved, but adding it to the reference database failed. "
                        "It can be retried later.", "warning")

                return redirect(url_for("dashboard.admin_dashboard"))

            elif action == "save":
                db.session.commit()
                flash("Assessment changes saved", "success")

                return redirect(url_for("issues.review_assessment", issue_id=issue.id))

            else:
                raise ValueError("Invalid form action")

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to review issue assessment")
            flash("Unable to save the assessment. Please try again.", "error")

            return redirect(url_for("issues.review_assessment", issue_id=issue.id))

    return render_template("issues/review_assessment.html", issue=issue, response=response)



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



@issues_bp.route("/pin/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def pin_issue(issue_id):   # pin issue

    issue = Issue.query.get_or_404(issue_id)
    issue.is_pinned = True

    db.session.commit()
    flash("Issue Pinned Successfully", "success")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))



@issues_bp.route("/unpin/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def unpin_issue(issue_id):    # unpin issue

    issue = Issue.query.get_or_404(issue_id)
    issue.is_pinned = False

    db.session.commit()
    flash("Manual prioritization removed", "info")

    return redirect(url_for("issues.issue_details", issue_id = issue.id))



@issues_bp.route("/hold/<int:issue_id>", methods = ['POST'])
@login_required
@admin_required
def hold_issue(issue_id):


    issue = Issue.query.get_or_404(issue_id)

    if issue.status != IssueStatus.IN_PROGRESS:
        flash("Only active issues can be placed on hold.", "warning")
        return redirect(url_for("issues.issue_details", issue_id=issue.id))

    old_status = issue.status
    now = ensure_utc(datetime.now(timezone.utc))
    HOLD_DURATION_DAYS = 3

    # Increase eligible time up to the moment the hold begins, then pause the clock.
    update_issue_priority(issue=issue, now=now)
    issue.status = IssueStatus.ON_HOLD
    issue.hold_until = now + timedelta(days=HOLD_DURATION_DAYS)
    issue.status_changed_at = now
    issue.aging_updated_at = None

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
    now = ensure_utc(datetime.now(timezone.utc))

    if issue.status == IssueStatus.IN_PROGRESS:
        update_issue_priority(issue=issue, now=now)
    
    issue.status = IssueStatus.RESOLVED
    issue.status_changed_at = now
    issue.aging_updated_at = None

    log_status_change(issue, old_status, issue.status, current_user.id, "Issue resolved")

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

    now = ensure_utc(datetime.now(timezone.utc))
    if issue.status == IssueStatus.IN_PROGRESS:
        update_issue_priority(issue=issue, now=now)

    issue.status = IssueStatus.CLOSED
    issue.status_changed_at = now
    issue.aging_updated_at = None
    
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
    now = ensure_utc(datetime.now(timezone.utc))
    issue.status = IssueStatus.IN_PROGRESS
    issue.hold_until = None
    issue.status_changed_at = now
    issue.aging_updated_at = now
    update_issue_priority(issue=issue, now=now)
    
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
from flask import Blueprint, redirect, url_for, render_template, request, flash, Response
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Building, Floor, Room, User
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import pandas as pd
import csv, io
from app.utils.decorators import admin_required
from app.org_setup.services import building_has_issues, floor_has_issues, room_has_issues



org_bp = Blueprint("org_setup", __name__)

 
def normalize_input(field):                     # remove white spaces, reuse helper func
    return request.form.get(field, "").strip()

@org_bp.route("/add-building", methods = ['GET', 'POST'])
@login_required
@admin_required
def add_building():

    if request.method == 'POST':

        name = normalize_input("name")                    
        is_active = request.form.get("is_active") == "on"            # default active status

        if not name:                                                 # Prevent blank names
            flash("Building name cannot be empty", "error")
            return redirect(url_for("org_setup.add_building"))
        
        existing = Building.query.filter(func.lower(Building.name) == name.lower()).first()     # lower check to avoid Block A and block A 

        if existing:
            flash(f'{name} already exists', "error")

        else:
            building = Building(name = name, is_active = is_active)

            try:
                db.session.add(building)
                db.session.commit()

                flash(f'{name} added successfully to buildings', "success")
                return redirect(url_for("org_setup.add_building"))                  # Prevent dup inserts after page refresh

            except IntegrityError:
                db.session.rollback()
                flash("Unexpected duplicate detected", "error")

    buildings = Building.query.all()
    
    return render_template("add_building.html", buildings = buildings)


@org_bp.route("/add-floor", methods = ['GET', 'POST'])
@login_required
@admin_required
def add_floor():

    buildings = Building.query.filter_by(is_active = True).all()

    if request.method == 'POST':

        number = normalize_input("number")
        building_id = request.form.get('building_id')

        if not building_id:                                  # Prevent adding floor without selecting a building
            flash("Please select a building", "error")
            return redirect(url_for("org_setup.add_floor") )
        building_id = int(building_id)

        is_active = request.form.get("is_active") == "on"

        if not number:
            flash("Floor number cannot be empty", "error")
            return redirect(url_for("org_setup.add_floor"))
        
        existing = Floor.query.filter(Floor.building_id == building_id, func.lower(Floor.number) == number.lower()).first()

        if existing:
            flash(f'Floor {number} already exists in this building', "error")

        else:
            floor = Floor( number = number, building_id = building_id, is_active = is_active)

            try:

                db.session.add(floor)
                db.session.commit()

                building = Building.query.get_or_404(building_id)               # Prevent crash for invalid ID , redirect to 404

                flash(f'Floor {number} added to {building.name} successfully', "success")
                return redirect(url_for("org_setup.add_floor"))
            
            except IntegrityError:
                db.session.rollback()
                flash("Database error occurred", "error")

    floors = Floor.query.all()

    return render_template("add_floor.html", buildings = buildings, floors = floors)


@org_bp.route("/add-room", methods = ['GET', 'POST'])
@login_required
@admin_required
def add_room():

    buildings = Building.query.filter_by(is_active = True).all()
    floors = Floor.query.join(Building).filter(Floor.is_active == True, Building.is_active == True).all() # Prevent active floors in inactive building from appearing

    if request.method == 'POST':

        name = normalize_input("name")
        floor_id = request.form.get("floor_id")

        if not floor_id:                                    # Prevents adding room without selecting floor
            flash("Please select a floor", "error")
            return redirect(url_for("org_setup.add_room"))
        floor_id = int(floor_id)

        is_active = request.form.get("is_active") == "on"

        if not name:
            flash("Room name cannot be empty", "error")
            return redirect(url_for("org_setup.add_room"))
        
        existing = Room.query.filter(Room.floor_id == floor_id, func.lower(Room.name) == name.lower()).first()

        if existing:
            flash(f'Room {name} already exists on this floor', "error")

        else:
            room = Room( name = name, floor_id = floor_id, is_active = is_active)

            try:

                db.session.add(room)
                db.session.commit()

                floor = Floor.query.get_or_404(floor_id)
                building = floor.building

                flash(f'Room {name} added to floor {floor.number} of {building.name} successfully', "success")
                return redirect(url_for("org_setup.add_room"))

            except IntegrityError:
                db.session.rollback()
                flash("Database error occurred", "error")

    rooms = Room.query.all()

    return render_template("add_room.html", buildings = buildings, floors = floors, rooms = rooms)

@org_bp.route("/upload-users", methods = ['GET', 'POST'])
@login_required
@admin_required
def upload_users():

    if request.method == 'POST':

        file = request.files.get("file")

        if not file:
            flash("No file uploaded", "error")
            return redirect(url_for("org_setup.upload_users"))
        
        try:
            df = pd.read_csv(file)                           # pd.read_csv(file, header=0) -> Use first row as column names
            df.columns = df.columns.str.strip().str.lower()  # Normalize column names, prevent excel from adding extra spaces

        except Exception:
            flash("Invalid CSV file", "error")
            return redirect(url_for("org_setup.upload_users"))
        
        required_columns = {"email"}

        if not required_columns.issubset(df.columns):
            flash("CSV file must contain email column", "error")
            return redirect(url_for("org_setup.upload_users"))
        
        added_count = 0
        duplicate_count = 0
        missing_email_count = 0
        invalid_course_end_date_count = 0

        for _, row in df.iterrows():                                       # _, row = index, row data
            email = row.get("email")

            if pd.isna(email) or str(email).strip() == "":
                missing_email_count += 1
                continue

            email = str(email).strip().lower()

            if email.startswith("example"):
                continue

            if "@" not in email:
                missing_email_count += 1
                continue

            existing_user = User.query.filter_by(email = email).first()

            if existing_user:
                duplicate_count += 1
                continue

            role = str(row.get("role", "user")).strip().lower()

            if role not in ["user", "admin"]:
                role = "user"

            is_active_raw = row.get("is_active")

            if pd.isna(is_active_raw) or str(is_active_raw).strip() == "":
                is_active = True

            else:
                is_active_value = str(is_active_raw).strip().lower()
                is_active = is_active_value in ["true", "1", "yes"]

            course_end_date = row.get("course_end_date")

            if pd.notna(course_end_date):

                parsed_date = pd.to_datetime(course_end_date, errors = "coerce")

                if pd.isna(parsed_date):
                    course_end_date = None
                    invalid_course_end_date_count += 1
                
                else:
                    course_end_date = parsed_date.date()

            else:
                course_end_date = None

            user = User(email = email, role = role, is_active = is_active, course_end_date = course_end_date)

            db.session.add(user)
            added_count += 1
        
        db.session.commit()

        flash(f'{added_count} users added, ' f'{duplicate_count} duplicates skipped, ' 
              f'{missing_email_count} rows missing email skipped, '
              f'{invalid_course_end_date_count} invalid course end date rows corrected', "success")
        
        return redirect(url_for("org_setup.upload_users"))
    
    return render_template("upload_users.html")

@org_bp.route("/download-user-template")
@login_required
@admin_required
def download_user_template():

    output = io.StringIO()                    # Creates a temp file in memory ( RAM )
    writer = csv.writer(output)               # Attaches a CSV writing tool to our temp file ( output )

    writer.writerow(["email", "role", "is_active", "course_end_date"])

    # Example row data in template for admins

    writer.writerow(["example1@college.edu.in", "user", "True", "2026-12-31"])
    writer.writerow(["example2@college.edu.in", "admin", "True", "2027-06-30"])

    output.seek(0)                          # After write pointer points end of file, so seek(0) to move pointer to start of file. Prevents downloading empty files
    
    return Response(output, mimetype = "text/csv",
                    headers = {"Content-Disposition" : "attachment; filename = user_upload_template.csv"}) # Header tells browser to download file and name it 



@org_bp.route("/user/deactivate/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def deactivate_user(user_id):

    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("You cannot deactivate your own active session.", "error")
    else:
        user.is_active = False
        db.session.commit()
        flash("User deactivated successfully", "info")

    return redirect(request.referrer or url_for("org_setup.manage_users"))


@org_bp.route("/user/reactivate/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def reactivate_user(user_id):

    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    
    flash("User reactivated successfully", "success")

    return redirect(request.referrer or url_for("org_setup.manage_users"))


@org_bp.route("/user/promote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def promote_user(user_id):

    user = User.query.get_or_404(user_id)
    user.role = "admin"
    db.session.commit()
    
    flash("User promoted to admin", "success")

    return redirect(request.referrer or url_for("org_setup.manage_users"))


@org_bp.route("/user/demote/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def demote_user(user_id):

    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash("You cannot demote yourself.", "error")
    else:
        user.role = "user"
        db.session.commit()
        flash("Administrator demoted back to user role", "success")

    return redirect(request.referrer or url_for("org_setup.manage_users"))


@org_bp.route("/building/rename/<int:id>", methods=["POST"])
@login_required
@admin_required
def rename_building(id):

    building = Building.query.get_or_404(id)

    new_name = request.form.get("name")

    building.name = new_name

    db.session.commit()

    flash("Building renamed successfully")

    return redirect(url_for("org_setup.manage_buildings"))




@org_bp.route("/floor/rename/<int:id>", methods=["POST"])
@login_required
@admin_required
def rename_floor(id):

    floor = Floor.query.get_or_404(id)

    new_name = request.form.get("name")

    floor.number = new_name

    db.session.commit()

    flash("Floor renamed successfully")

    return redirect(url_for("org_setup.manage_floors"))




@org_bp.route("/room/rename/<int:id>", methods=["POST"])
@login_required
@admin_required
def rename_room(id):

    room = Room.query.get_or_404(id)

    new_name = request.form.get("name")

    room.name = new_name

    db.session.commit()

    flash("room renamed successfully")

    return redirect(url_for("org_setup.manage_rooms"))



@org_bp.route("/building/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_building(id):

    building = Building.query.get_or_404(id)

    if building_has_issues(building):
        flash(f"Cannot delete {building.name} because issues exists under this location. Deactivate instead.", "error")
        return redirect(url_for("org_setup.manage_buildings"))

    db.session.delete(building)

    db.session.commit()

    flash(f"{building.name} deleted permanently", "success")

    return redirect(url_for("org_setup.manage_buildings"))




@org_bp.route("/floor/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_floor(id):

    floor = Floor.query.get_or_404(id)

    if floor_has_issues(floor):
        flash(f"Cannot delete {floor.number} because issues exists under this location. Deactivate instead.", "error")
        return redirect(url_for("org_setup.manage_floors"))

    db.session.delete(floor)

    db.session.commit()

    flash(f"{floor.number} deleted permanently", "success")

    return redirect(url_for("org_setup.manage_floors"))



@org_bp.route("/room/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_room(id):

    room = Room.query.get_or_404(id)

    if room_has_issues(room):
        flash(f"Cannot delete {room.name} because issues exists under this location.", "error")
        return redirect(url_for("org_setup.manage_rooms"))

    db.session.delete(room)

    db.session.commit()

    flash(f"{room.name} deleted permanently", "success")

    return redirect(url_for("org_setup.manage_rooms"))



@org_bp.route("/building/deactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def deactivate_building(id):

    building = Building.query.get_or_404(id)

    building.is_active = False

    db.session.commit()

    flash(f"{building.name} hidden from users")

    return redirect(url_for("org_setup.manage_buildings"))



@org_bp.route("/floor/deactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def deactivate_floor(id):

    floor = Floor.query.get_or_404(id)

    floor.is_active = False

    db.session.commit()

    flash(f"{floor.number} hidded from users")

    return redirect(url_for("org_setup.manage_floors"))



@org_bp.route("/room/deactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def deactivate_room(id):

    room = Room.query.get_or_404(id)

    room.is_active = False

    db.session.commit()

    flash(f"{room.name} hidded from users")

    return redirect(url_for("org_setup.manage_rooms"))



@org_bp.route("/building/reactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def reactivate_building(id):

    building = Building.query.get_or_404(id)

    building.is_active = True

    db.session.commit()

    flash(f"{building.name} made visible to users")

    return redirect(url_for("org_setup.manage_buildings"))



@org_bp.route("/floor/reactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def reactivate_floor(id):

    floor = Floor.query.get_or_404(id)

    floor.is_active = True

    db.session.commit()

    flash(f"{floor.number} made visible to users")

    return redirect(url_for("org_setup.manage_floors"))



@org_bp.route("/room/reactivate/<int:id>", methods=["POST"])
@login_required
@admin_required
def reactivate_room(id):

    room = Room.query.get_or_404(id)

    room.is_active = True

    db.session.commit()

    flash(f"{room.name} made visible to users")

    return redirect(url_for("org_setup.manage_rooms"))

@org_bp.route("/manage-buildings", methods=["GET"])
@login_required
@admin_required
def manage_buildings():
    buildings = Building.query.all()
    return render_template("manage_buildings.html", buildings=buildings)

@org_bp.route("/manage-floors", methods=["GET"])
@login_required
@admin_required
def manage_floors():
    building_id = request.args.get("building_id")
    buildings = Building.query.all()
    if building_id:
        floors = Floor.query.filter_by(building_id=building_id).all()
    else:
        floors = Floor.query.all()
    return render_template("manage_floors.html", floors=floors, buildings=buildings, selected_building_id=building_id)

@org_bp.route("/manage-rooms", methods=["GET"])
@login_required
@admin_required
def manage_rooms():
    building_id = request.args.get("building_id")
    floor_id = request.args.get("floor_id")
    
    buildings = Building.query.all()
    floors = []
    query = Room.query
    
    if building_id:
        floors = Floor.query.filter_by(building_id=building_id).all()
        if floor_id and any(str(f.id) == floor_id for f in floors):
            query = query.filter_by(floor_id=floor_id)
        else:
            floor_ids = [f.id for f in floors]
            query = query.filter(Room.floor_id.in_(floor_ids) if floor_ids else False)
    
    rooms = query.all()
    return render_template("manage_rooms.html", rooms=rooms, buildings=buildings, floors=floors, selected_building_id=building_id, selected_floor_id=floor_id)

@org_bp.route("/manage-users", methods=["GET"])
@login_required
@admin_required
def manage_users():
    search_query = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "all").strip()
    
    query = User.query
    if search_query:
        query = query.filter(User.email.ilike(f"%{search_query}%"))
        
    if role_filter != "all":
        query = query.filter(User.role == role_filter)
        
    users = query.all()
    return render_template("manage_users.html", users=users, search_query=search_query, current_role=role_filter)
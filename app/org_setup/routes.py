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

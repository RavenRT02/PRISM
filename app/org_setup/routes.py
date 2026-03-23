from flask import Blueprint, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models import Building, Floor, Room
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

org_bp = Blueprint("org_setup", __name__)

def admin_required(func):           # custom decorator to check admin role , will be used with buildings, floors and rooms page access
    
    @wraps(func)
    def wrapper(*args, **kwargs):

        if current_user.role != "admin":
            return "Access denied", 403        # not admin - deny access #return redirect(url_for("auth.dashboard")) - not admin - redirect
        
        return func(*args, **kwargs)                                # admin - run original function
    
                                                # wrapper.__name__ = func.__name__  set wrapper name to original func name(manually without @wraps)
    return wrapper                                           # runs after decorator is applied not after all the above conditions

 
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
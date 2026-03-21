from flask import Blueprint, redirect, url_for, render_template, request, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Building

org_bp = Blueprint("org_setup", __name__)

def admin_required(func):           # custom decorator to check admin role , will be used with buildings, floors and rooms page access
    def wrapper(*args, **kwargs):

        if current_user.role != "admin":
            return "Access denied", 403        # not admin - deny access #return redirect(url_for("auth.dashboard")) - not admin - redirect
        
        return func(*args, **kwargs)                                # admin - run original function
    
    wrapper.__name__ = func.__name__                                # set wrapper name to original func name 
    return wrapper                                           # runs after decorator is applied not after all the above conditions


@org_bp.route("/add-building", methods = ['GET', 'POST'])
@login_required
@admin_required
def add_building():

    if request.method == 'POST':

        name = request.form.get("name")
        is_active = request.form.get("is_active") == "on" 

        building = Building(name = name, is_active = is_active)

        db.session.add(building)
        db.session.commit()

        flash(f'{name} added Successfully to buildings', "Success")

    buildings = Building.query.all()
    
    return render_template("add_building.html", buildings = buildings)
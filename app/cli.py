from app.extensions import db
from app.models import IssueCategory
from flask import current_app
from flask.cli import with_appcontext
import click

@click.command("seed-categories")
@with_appcontext
def seed_categories():

    categories = ["Infrastructure",
                    "Electrical",
                    "Water",
                    "Cleaning",
                    "Furniture",
                    "IT Services",
                    "Safety",
                    "Other"]
    
    for name in categories:

        exists = IssueCategory.query.filter_by(name = name).first()

        if not exists:
            db.session.add(IssueCategory(name = name))

    db.session.commit()

    click.echo("Default issue categories added")
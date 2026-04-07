from flask_login import UserMixin    # provides flask_login req methods like is_authenticated,is_active,is_anonymous,get_id()
                                     # flask_login does not recognise the model as user without UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db,login_manager
from datetime import datetime, timezone
from app.issues.enums import IssueStatus, IssueType, PriorityLevel


class User(UserMixin, db.Model):           # users table

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    password_hash = db.Column(db.String(255), nullable = True)

    is_password_set = db.Column(db.Boolean, default = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

    course_end_date = db.Column(db.Date, nullable = True )

    created_at = db.Column(db.DateTime, default = lambda: datetime.now(timezone.utc))

    issues = db.relationship("Issue", foreign_keys = "Issue.created_by", lazy = True)

    verified_issues = db.relationship("Issue", foreign_keys = "Issue.verified_by", lazy = True)

    followed_issues = db.relationship("IssueFollower", foreign_keys = "IssueFollower.user_id", lazy = True)


    def set_password(self,password):                         # Convert user pass to hashed pass before storing in db
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):                       # Check if user pass matches hashed pass in db at login
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<user {self.email}>"
    
    
@login_manager.user_loader                   # Tells flask_login on how to retrieve user from db
def load_user(user_id):
    return User.query.get(int(user_id))



class UserOTP(db.Model):

    __tablename__ = "user_otps"

    id = db.Column(db.Integer, primary_key = True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False, index = True)

    otp_hash = db.Column(db.String(128), nullable = False)

    purpose = db.Column(db.String(30), nullable = False)

    expires_at = db.Column(db.DateTime(timezone = True), nullable = False)

    attempts = db.Column(db.Integer, default = 0, nullable = False)

    is_used = db.Column(db.Boolean, default = False, nullable = False)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref = "otps")

    __table_args__ = (db.Index("idx_user_purpose_active", "user_id", "purpose", "is_used"),)



class Building(db.Model):

    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(100), nullable = False, unique = True)

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    floors = db.relationship("Floor", back_populates = "building", lazy=True)


class Floor(db.Model):

    __tablename__ = "floors"

    id = db.Column(db.Integer, primary_key = True)

    number = db.Column(db.String(20), nullable = False)

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    building = db.relationship("Building", back_populates = "floors")

    __table_args__ = (db.UniqueConstraint("number", "building_id", name = "uq_floor_building"),)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    rooms = db.relationship("Room", back_populates = "floor", lazy=True)


class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(50), nullable = False)

    floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    floor = db.relationship("Floor", back_populates = "rooms")

    __table_args__ = (db.UniqueConstraint("name", "floor_id", name = "uq_room_floor"),)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    issues = db.relationship("Issue", back_populates = "room", lazy = True)



class IssueCategory(db.Model):

    __tablename__ = "issue_categories"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(100), unique = True, nullable = False)

    description = db.Column(db.String(255))

    display_order = db.Column(db.Integer, default = 0)

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))




class Issue(db.Model):

    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key = True)

    title = db.Column(db.String(150), nullable = True)

    description = db.Column(db.String(300), nullable = False)

    issue_type = db.Column(db.Enum(IssueType), nullable = False)

    category_id = db.Column(db.Integer, db.ForeignKey("issue_categories.id"), nullable = False)
    category = db.relationship("IssueCategory")

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable = False)
    building = db.relationship("Building")

    floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable = False)
    floor = db.relationship("Floor")

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable = False)
    room = db.relationship("Room", back_populates = "issues")

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    creator = db.relationship("User", foreign_keys = [created_by], overlaps = "issues")

    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    verifier = db.relationship("User", foreign_keys = [verified_by], overlaps = "verified_issues")

    status = db.Column(db.Enum(IssueStatus), default = IssueStatus.SUBMITTED, nullable = False)

    urgency_score = db.Column(db.Integer)

    impact_score = db.Column(db.Integer)

    aging_score = db.Column(db.Integer, default = 0)

    priority_score = db.Column(db.Integer)

    priority_level = db.Column(db.Enum(PriorityLevel))

    priority_override = db.Column(db.Boolean, default = False)

    image_path = db.Column(db.String(255))

    review_notes = db.Column(db.String(300))

    hold_until = db.Column(db.DateTime(timezone = True))

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    verified_at = db.Column(db.DateTime(timezone = True))

    approved_at = db.Column(db.DateTime(timezone = True))

    updated_at = db.Column(db.DateTime(timezone = True), onupdate = lambda: datetime.now(timezone.utc))

    status_changed_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    followers = db.relationship("IssueFollower", foreign_keys = "IssueFollower.issue_id", lazy = True)



class IssueFollower(db.Model):

    __tablename__ = "issue_followers"

    id = db.Column(db.Integer, primary_key = True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)

    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable = False)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    user = db.relationship("User", overlaps = "followed_issues")
    issue = db.relationship("Issue", overlaps = "followers")

    __table_args__ = (db.UniqueConstraint("user_id", "issue_id", name = "uq_user_issue_follow"), )



class IssueStatusHistory(db.Model):

    __tablename__ = "issue_status_history"

    id = db.Column(db.Integer, primary_key=True)

    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)

    old_status = db.Column(db.String(50))

    new_status = db.Column(db.String(50), nullable=False)

    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    changed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    note = db.Column(db.String(255))
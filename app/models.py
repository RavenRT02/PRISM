from flask_login import UserMixin    # provides flask_login req methods like is_authenticated,is_active,is_anonymous,get_id()
                                     # flask_login does not recognise the model as user without UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db,login_manager
from datetime import datetime, timezone
from app.issues.enums import IssueStatus, IssueType, PriorityLevel, LocationScope


# db.Model -- Makes the class a SQLAlchemy database model

class User(UserMixin, db.Model):           # users table

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)

    email = db.Column(db.String(120), unique = True, nullable = False)

    password_hash = db.Column(db.String(255), nullable = True)

    is_password_set = db.Column(db.Boolean, default = False)

    role = db.Column(db.String(20), nullable = False, default = "user")

    is_active = db.Column(db.Boolean, default = True)

    course_end_date = db.Column(db.Date, nullable = True )

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    # db.relationship -- Creates a Python/SQLAlchemy relationship to another model
    # They do not create columns, They create SQLAlchemy/Python navigation paths.

    # "From a users object, let me access the issues that this user created." -- Show issues created by this user
    # user.issues -- Give me the issues whose issues.created_by points to this users.id.
    # FK in this table are not inside [] as they reference other table columns
    issues = db.relationship("Issue", foreign_keys = "Issue.created_by", back_populates = "creator", lazy = True)

    # Show issues verified by this user
    verified_issues = db.relationship("Issue", foreign_keys = "Issue.verified_by", back_populates = "verifier", lazy = True)

    # Show issues followed by this user -- No need to explictly define FK here since there is only 1 FK from IssueFollowers to User
    followed_issues = db.relationship("IssueFollower", foreign_keys = "IssueFollower.user_id", back_populates = "user", lazy = True)

    otps = db.relationship("UserOTP", back_populates = "user", lazy = True)

    status_changes = db.relationship("IssueStatusHistory", back_populates = "changer", lazy = True)


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

    # back_populates is cleaner for complex db designs as it is defined on both sides. 
    user = db.relationship("User", back_populates = "otps")

    # __table_agrs__ -- Gives table-level configuration/constraints to SQLAlchemy 
    # Ending comma necessary since __table_args__ have to be tuple or dict, without comma it will not be a tuple 
    # __table_args__ = (value,) 
    __table_args__ = (db.Index("idx_user_purpose_active", "user_id", "purpose", "is_used"),)



class Building(db.Model):

    __tablename__ = "buildings"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(100), nullable = False, unique = True)

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    # back_populates -- explicitly define on both sides ( defined in floors table as well )
    # lazy=True is SQLAlchemy, not a database feature. It controls when SQLAlchemy loads the related objects.
    floors = db.relationship("Floor", back_populates = "building", lazy=True)


class Floor(db.Model):

    __tablename__ = "floors"

    id = db.Column(db.Integer, primary_key = True)

    number = db.Column(db.String(20), nullable = False)

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    # Explicitly defined here ( also in buildings table )
    building = db.relationship("Building", back_populates = "floors")

    rooms = db.relationship("Room", back_populates = "floor", lazy=True)

    __table_args__ = (db.UniqueConstraint("number", "building_id", name = "uq_floor_building"),)


class Room(db.Model):

    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(50), nullable = False)

    floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable = False)

    is_active = db.Column(db.Boolean, default = True)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    floor = db.relationship("Floor", back_populates = "rooms")

    issues = db.relationship("Issue", back_populates = "room", lazy = True)

    __table_args__ = (db.UniqueConstraint("name", "floor_id", name = "uq_room_floor"),)



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

    location_scope = db.Column(db.Enum(LocationScope), nullable = False)

    status = db.Column(db.Enum(IssueStatus), default = IssueStatus.SUBMITTED, nullable = False)

    safety_score = db.Column(db.Float, nullable = True)

    impact_score = db.Column(db.Float, nullable = True)

    urgency_score = db.Column(db.Float, nullable = True)

    aging_score = db.Column(db.Float, nullable = False, default = 0.0)

    priority_score = db.Column(db.Float, nullable = True)

    priority_level = db.Column(db.Enum(PriorityLevel))

    is_pinned = db.Column(db.Boolean, nullable = False, default = False)

    image_path = db.Column(db.String(255))

    review_notes = db.Column(db.String(300))

    hold_until = db.Column(db.DateTime(timezone = True))

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    verified_at = db.Column(db.DateTime(timezone = True))

    updated_at = db.Column(db.DateTime(timezone = True), onupdate = lambda: datetime.now(timezone.utc))

    status_changed_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    # Last time eligible IN_PROGRESS time was converted into aging points.
    aging_updated_at = db.Column(db.DateTime(timezone = True))

    # Admin's optional duplicate suggestion
    suggested_duplicate_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable = True)

    # User decision - Pending, Accepted or Declined to suggested duplicate tracking
    duplicate_suggestion_status = db.Column(db.String(20), nullable = True)

    # Flag to hide issues from user dashboard when they delete issue in UI 
    hidden_from_user = db.Column(db.Boolean, nullable = False, default = False, server_default = db.false())


    category_id = db.Column(db.Integer, db.ForeignKey("issue_categories.id"), nullable = False)
    category = db.relationship("IssueCategory")

    building_id = db.Column(db.Integer, db.ForeignKey("buildings.id"), nullable = False)
    building = db.relationship("Building")

    floor_id = db.Column(db.Integer, db.ForeignKey("floors.id"), nullable = True)
    floor = db.relationship("Floor")

    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable = True)
    room = db.relationship("Room", back_populates = "issues")

    """
    foreign_keys = [column] The square brackets make it a Python list containing that column.
    SQLAlchemy's foreign_keys parameter accepts a collection of columns because 
    a relationship can involve one or more ForeignKey columns.
    for users table created_by was not inside the table so Issue.created_by
    This table on the otherhand has created_by within it so [column]
    """

    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    creator = db.relationship("User", foreign_keys = [created_by], back_populates = "issues")

    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    verifier = db.relationship("User", foreign_keys = [verified_by], back_populates = "verified_issues")

    followers = db.relationship("IssueFollower", foreign_keys = "IssueFollower.issue_id", back_populates = "issue", lazy = True)

    suggested_duplicate = db.relationship("Issue", foreign_keys = [suggested_duplicate_id], remote_side = "Issue.id")

    status_history = db.relationship("IssueStatusHistory", back_populates = "issue", lazy = True)

    llm_response = db.relationship("LLMResponse", back_populates= "issue", uselist= False, cascade= "all, delete-orphan")


    __table_args__ = (
        db.CheckConstraint(
            """
            (location_scope = 'BUILDING' AND floor_id IS NULL AND room_id IS NULL)
            OR
            (location_scope = 'FLOOR' AND floor_id IS NOT NULL AND room_id IS NULL)
            OR
            (location_scope = 'ROOM' AND floor_id IS NOT NULL AND room_id IS NOT NULL)
            """,
            name = "ck_issue_location_scope"
        ),
    )



class LLMResponse(db.Model):

    __tablename__ = "llm_responses"

    id = db.Column(db.Integer, primary_key=True)

    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id", ondelete= "CASCADE"), nullable= False, unique= True)

    # Preserve the original issue description and scope
    description = db.Column(db.String(300), nullable=False)
    scope = db.Column(db.Enum(LocationScope), nullable=False)

    # LLM-proposed or admin-edited factor ranges
    safety_min = db.Column(db.Float, nullable=False)
    safety_max = db.Column(db.Float, nullable=False)

    impact_min = db.Column(db.Float, nullable=False)
    impact_max = db.Column(db.Float, nullable=False)

    urgency_min = db.Column(db.Float, nullable=False)
    urgency_max = db.Column(db.Float, nullable=False)

    # Calculated midpoints
    safety_score = db.Column(db.Float, nullable=False)
    impact_score = db.Column(db.Float, nullable=False)
    urgency_score = db.Column(db.Float, nullable=False)

    # Calculated overall priority
    priority_score = db.Column(db.Float, nullable=False)
    priority_level = db.Column(db.Enum(PriorityLevel), nullable=False)

    # Approval and vector-store ingestion tracking
    finalized = db.Column(db.Boolean, nullable=False, default=False)
    added_to_vector_db = db.Column(db.Boolean, nullable=False, default=False)

    # Relationship to the original issue
    issue = db.relationship("Issue", back_populates= "llm_response")



class IssueFollower(db.Model):

    __tablename__ = "issue_followers"

    id = db.Column(db.Integer, primary_key = True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)

    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable = False)

    created_at = db.Column(db.DateTime(timezone = True), default = lambda: datetime.now(timezone.utc))

    user = db.relationship("User", foreign_keys = [user_id], back_populates = "followed_issues")
    issue = db.relationship("Issue", foreign_keys = [issue_id], back_populates = "followers")

    __table_args__ = (db.UniqueConstraint("user_id", "issue_id", name = "uq_user_issue_follow"), )



class IssueStatusHistory(db.Model):

    __tablename__ = "issue_status_history"

    id = db.Column(db.Integer, primary_key=True)

    issue_id = db.Column(db.Integer, db.ForeignKey("issues.id"), nullable=False)

    old_status = db.Column(db.Enum(IssueStatus), nullable = True)

    new_status = db.Column(db.Enum(IssueStatus), nullable=False)

    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = True)

    changed_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    note = db.Column(db.String(255))

    issue = db.relationship("Issue", back_populates = "status_history")

    changer = db.relationship("User", back_populates = "status_changes")
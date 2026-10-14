## SQLAlchemy model

db.Model
→ Makes a Python class a SQLAlchemy model representing a database table.

__tablename__
→ Specifies the actual database table name.

Example: User → "users".

Database structure through SQLAlchemy

db.Column(...)
→ Defines a database column.

db.ForeignKey("users.id")
→ Database relationship/constraint: this column references users.id.

db.Index(...)
→ Database index; improves certain searches.

db.UniqueConstraint(...)
→ Database rule requiring a combination of columns to be unique.

__table_args__
→ SQLAlchemy place for table-level things such as Index and UniqueConstraint.

## SQLAlchemy ORM / navigation

db.relationship("Model")
→ Creates a Python/SQLAlchemy way to navigate to related objects. It is separate from the ForeignKey itself.

foreign_keys=...
→ Tells SQLAlchemy which ForeignKey a particular relationship should use, especially when multiple ForeignKeys connect the same two tables.

Example:

issues.created_by → users.id
creator = db.relationship("User", foreign_keys=[created_by])

back_populates
→ Explicitly connects the two sides of a SQLAlchemy relationship.

Building.floors ↔ Floor.building

Both sides are written.

backref
→ Define one side; SQLAlchemy automatically creates the reverse attribute.

user = db.relationship("User", backref="otps")

creates User.otps.

lazy
→ Controls when SQLAlchemy loads related objects. It does not create the database relationship.

overlaps
→ Tells SQLAlchemy that two relationship definitions intentionally refer to overlapping underlying relationships/columns. It is not a database constraint.

important example

For:

issues.created_by → users.id

think:

db.ForeignKey(...) → DATABASE → "These columns are related."


db.relationship(...) → SQLALCHEMY → "Let Python navigate between these related objects."


foreign_keys=... → SQLALCHEMY → "Use THIS particular ForeignKey."


back_populates / backref → SQLALCHEMY → "How should the reverse side of this relationship be represented?"


lazy=... → SQLALCHEMY → "When should the related objects be loaded?"


overlaps=... → SQLALCHEMY → "These relationship definitions overlap intentionally."

remember only one thing: 
- ForeignKey establishes the database-side connection; 
- relationship() establishes the ORM/Python-side navigation. 
- The other terms (foreign_keys, back_populates, backref, lazy, overlaps) are options that tell SQLAlchemy how to handle that Python-side relationship


## Removed backref and overlaps to use back_populates everywhere to keep things consistent (code before change)

    # overalps -- These relationship definitions overlap with another relationship definition, and this is intentional.
    # overlaps="issues" tells SQLAlchemy that Issue.creator overlaps with User.issues.
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    creator = db.relationship("User", foreign_keys = [created_by], overlaps = "issues")

    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    verifier = db.relationship("User", foreign_keys = [verified_by], overlaps = "verified_issues")

    user = db.relationship("User", overlaps = "followed_issues")
    issue = db.relationship("Issue", overlaps = "followers")

    # backref -- define one side, SQLAlchemy creates the reverse attribute automatically. (on users table)
    # back_populates is cleaner for complex db designs as it is defined on both sides. 
    user = db.relationship("User", backref = "otps")
import enum

# The application has concepts with a fixed, finite set of valid values, 
# so Python's Enum gives those concepts an explicit type and namespace.
# Enums define a fixed set of valid choices and group related values.
# They provide type safety and make the code clearer than using plain constants.


class IssueStatus(enum.Enum):

    SUBMITTED = "SUBMITTED"
    PRIORITIZED = "PRIORITIZED"   # requires change ( IN_PROGRESS )
    ON_HOLD = "ON_HOLD"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"

class IssueType(enum.Enum):

    COMPLAINT = "COMPLAINT"
    REQUEST = "REQUEST"

class PriorityLevel(enum.Enum):

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
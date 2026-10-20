import enum

# The application has concepts with a fixed, finite set of valid values, 
# so Python's Enum gives those concepts an explicit type and namespace.
# Enums define a fixed set of valid choices and group related values.
# They provide type safety and make the code clearer than using plain constants.


class IssueStatus(enum.Enum):

    SUBMITTED = "SUBMITTED"
    IN_PROGRESS = "IN_PROGRESS"   # Previously PRIORITIZED
    PENDING_APPROVAL = "PENDING_APPROVAL"  # new state for llm response waiting for admin approval
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

class LocationScope(enum.Enum):

    BUILDING = "BUILDING"
    FLOOR = "FLOOR"
    ROOM = "ROOM"
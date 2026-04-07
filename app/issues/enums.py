import enum

class IssueStatus(enum.Enum):

    SUBMITTED = "SUBMITTED"
    PRIORITIZED = "PRIORITIZED"
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
    MEDIUM = "MIDIUM"
    LOW = "LOW"
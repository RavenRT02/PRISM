def get_user_visible_status(issue):

    if issue.status.name == "SUBMITTED":
        return "Under review"

    if issue.status.name == "PRIORITIZED":
        return "Approved"

    if issue.status.name == "ON_HOLD":
        return "Approved"

    if issue.status.name == "RESOLVED":
        return "Resolved"

    if issue.status.name == "CLOSED":
        return "Closed"

    if issue.status.name == "REJECTED":
        return "Rejected"

    return issue.status.name
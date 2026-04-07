from datetime import timezone

def ensure_utc(dt):  
    """helper func to attach utc label to naive datetime ( does not convert time, attaches utc label )
        adds utc label to naive datetime and does not affect aware datetime, handles db and py datetime conflict"""        

    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt
from datetime import timezone
from zoneinfo import ZoneInfo

def ensure_utc(dt):  
    """helper func to attach utc label to naive datetime ( does not convert time, attaches utc label )
        adds utc label to naive datetime and does not affect aware datetime, handles db and py datetime conflict"""        

    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt



def format_local_datetime(value):
    if value is None:
        return ""

    # SQLite commonly returns naive datetimes; your app stores these in UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%b %d, %Y %I:%M %p")
from app.models import Floor, Room, Issue


def building_has_issues(building):

    for floor in building.floors:

        for room in floor.rooms:

            if room.issues:
                return True

    return False



def floor_has_issues(floor):

    for room in floor.rooms:

        if room.issues:
            return True

    return False



def room_has_issues(room):

    return bool(room.issues)
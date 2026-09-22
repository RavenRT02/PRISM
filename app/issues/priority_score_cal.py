# This file was created to calculate deterministic priority score that will be imported and used in priority_engine.py

# imports
from app.issues.enums import PriorityLevel


def find_midpoint(safety_range: list[int], impact_range: list[int], urgency_range: list[int]) -> tuple[float, float, float]:
    """
    Gets the list of lower and upper limit scores for each factor from the reference dataset 
    and calculates the midpoint 
    """

    safety = (safety_range[0] + safety_range[1]) / 2
    impact = (impact_range[0] + impact_range[1]) / 2
    urgency = (urgency_range[0] + urgency_range[1]) / 2

    return safety, impact, urgency



def calculate_priority_score(safety: float, impact: float, urgency: float) -> tuple[float, PriorityLevel]:
    """
    Calculate the initial priority score from Safety, Impact, and Urgency.
    Each factor is expected to be a score from 0 to 100.
    The parameters for this function are midpoints from "find_midpoint" hence the float type
    """

    base_score = (safety*0.40 + impact*0.25 + urgency*0.25)

    high_factor_count = sum ( 
        score >= 70 for score in (safety, impact, urgency) 
        )

    if high_factor_count == 2:
        bonus = 2
    elif high_factor_count == 3:
        bonus = 3
    else:
        bonus = 0

    initial_score = min(base_score + bonus, 90)

    if initial_score <= 25:
        priority_level = PriorityLevel.LOW
    elif initial_score <= 55:
        priority_level = PriorityLevel.MEDIUM
    elif initial_score <= 75:
        priority_level = PriorityLevel.HIGH
    else:
        priority_level = PriorityLevel.CRITICAL

    return round(initial_score, 2), priority_level.value
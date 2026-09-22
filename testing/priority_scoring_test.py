# run with --> python -m testing.priority_scoring_test
# app is not inside testing folder so it cannot find when this file is run with the run button

from app.issues.priority_score_cal import find_midpoint
from app.issues.priority_score_cal import calculate_priority_score


tests = [
    # Exactly 25
    [[25, 25], [25, 25], [25, 25]],

    # Exactly 26
    [[26, 26], [26, 26], [26, 26]],

    # Exactly 55
    [[55, 55], [55, 55], [55, 55]],

    # Exactly 56
    [[56, 56], [56, 56], [56, 56]],

    # Exactly 75
    [[75, 75], [75, 75], [75, 75]],

    # Exactly 76
    [[76, 76], [76, 76], [76, 76]],

    # Should trigger +3 bonus but remain below 90
    [[85, 85], [85, 85], [85, 85]],

    # Should trigger the 90 cap
    [[100, 100], [100, 100], [100, 100]],

    # Mixed factors: exactly 2 high factors
    [[80, 80], [80, 80], [60, 60]],

    # Mixed factors: exactly 1 high factor
    [[80, 80], [60, 60], [60, 60]],
]


for safety_range, impact_range, urgency_range in tests:

    safety, impact, urgency = find_midpoint(safety_range=safety_range, impact_range=impact_range, urgency_range=urgency_range)

    score, level = calculate_priority_score(safety=safety, impact=impact, urgency=urgency)

    print(f"Safety={safety}, Impact={impact}, Urgency={urgency} -> Score={score}, Level={level}")
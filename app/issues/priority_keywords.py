URGENCY_KEYWORDS = {
    "health": {
        "keywords": [
            "chemical", "spill", "injury", "blood", "infect", "gas leak", 
            "fume", "breath", "unconscious", "burn", "acid", "hazard", 
            "toxic", "accident", "pest", "insect", "snake", "mosquito", "rodent"
        ],
        "score": 5
    },
    "safety": {
        "keywords": [
            "electric", "shock", "fire", "spark", "short circuit", "wire expose", 
            "overheat", "smoke", "alarm", "explode", "loose wire", "trip hazard", 
            "block exit", "lock", "guard", "security", "theft", "steal"
        ],
        "score": 4
    },
    "basic_needs": {
        "keywords": [
            "water", "toilet", "restroom", "washroom", "drink", "power", 
            "electricity", "fan", "light", "ac", "wifi", "internet", 
            "network", "outage", "down", "food", "mess", "hygiene", "bed"
        ],
        "score": 3
    },
    "unrest": {
        "keywords": [
            "fight", "violent", "crowd", "protest", "argue", "harass", 
            "threat", "rag", "bully", "disturb", "panic"
        ],
        "score": 5
    },
    "academic_critical": {
        "keywords": [
            "server", "portal", "login", "exam", "fee", "block", "crash", 
            "projector", "pc", "software", "id", "card"
        ],
        "score": 4
    }
}


IMPACT_KEYWORDS = {
    "severity": {
        "keywords": [
            "collapse", "break", "leak", "damage", "crack", "flood", 
            "overflow", "fail", "malfunction", "shutdown", "fix", 
            "error", "bug", "corrupt"
        ],
        "score": 3
    },
    "escalation": {
        "keywords": [
            "spread", "increase", "worsen", "affect", "multiple", 
            "mass", "campuswide", "hostelwide"
        ],
        "score": 2
    },
    "long_term": {
        "keywords": [
            "structure", "foundation", "permanent", "ceiling", "wall", 
            "building", "pipe", "seep"
        ],
        "score": 4
    },
    "service_disruption": {
        "keywords": [
            "interrupt", "cancel", "close", "unavailable", "delay", 
            "pause", "halt", "suspend"
        ],
        "score": 3
    }
}
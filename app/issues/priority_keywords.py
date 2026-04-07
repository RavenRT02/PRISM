URGENCY_KEYWORDS = {

    "health": {
        "keywords": [
            "chemical",
            "spill",
            "injury",
            "blood",
            "infection",
            "gas leak",
            "fumes",
            "breathing problem",
            "unconscious",
            "burn",
            "acid",
            "hazardous",
            "toxic",
            "lab accident"
        ],
        "score": 5
    },

    "safety": {
        "keywords": [
            "electric",
            "shock",
            "fire",
            "sparking",
            "short circuit",
            "wire exposed",
            "overheating",
            "smoke",
            "alarm",
            "explosion risk",
            "loose wiring",
            "trip hazard",
            "blocked exit",
            "emergency exit locked"
        ],
        "score": 4
    },

    "basic_needs": {
        "keywords": [
            "water",
            "toilet",
            "restroom",
            "washroom",
            "drinking water",
            "no water",
            "power outage",
            "electricity",
            "fan not working",
            "light not working",
            "ac not working",
            "wifi down",
            "network issue"
        ],
        "score": 3
    },

    "unrest": {
        "keywords": [
            "fight",
            "violence",
            "crowd",
            "protest",
            "argument",
            "harassment",
            "threat",
            "ragging",
            "bullying",
            "disturbance",
            "panic"
        ],
        "score": 5
    }
}


IMPACT_KEYWORDS = {

    "severity": {
        "keywords": [
            "collapsed",
            "broken",
            "leak",
            "damage",
            "crack",
            "flooding",
            "overflow",
            "not working",
            "failed",
            "malfunction",
            "shutdown"
        ],
        "score": 3
    },

    "escalation": {
        "keywords": [
            "spreading",
            "increasing",
            "worsening",
            "getting worse",
            "affecting nearby",
            "affecting multiple rooms",
            "affecting students",
            "affecting floor",
            "affecting building"
        ],
        "score": 2
    },

    "long_term": {
        "keywords": [
            "structural",
            "foundation",
            "permanent",
            "ceiling crack",
            "wall crack",
            "building damage",
            "pipeline damage",
            "seepage",
            "water seepage"
        ],
        "score": 4
    },

    "service_disruption": {
        "keywords": [
            "class interrupted",
            "lab cancelled",
            "exam affected",
            "hostel issue",
            "canteen closed",
            "library closed",
            "wifi unavailable"
        ],
        "score": 3
    }
}
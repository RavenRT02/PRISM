from better_profanity import profanity

profanity.load_censor_words()

CUSTOM_BLOCKED_PHRASES = {"worst college", "useless admin", "hate this place"}

def contains_toxicity(text: str) -> bool:

    if profanity.contains_profanity(text):
        return True
    
    lowered = text.lower()

    return any(phrase in lowered for phrase in CUSTOM_BLOCKED_PHRASES)
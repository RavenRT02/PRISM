import re
from functools import lru_cache
from app.issues.priority_engine import clean_and_lemmatize


STOPWORDS = { "the", "is", "in", "at", "on", "a", "an", "and", "or", "to", "for", "of", "with", "by", "from" }

@lru_cache(maxsize=1024)
def normalize(text):
    if not text:
        return set()
    
    lemmatized_text = clean_and_lemmatize(text)
    
    words = lemmatized_text.split()
    cleaned_words = { word for word in words if word not in STOPWORDS and len(word) > 2 }
    return cleaned_words


def overlap_coefficient(text1, text2):
    
    words1 = normalize(text1)
    words2 = normalize(text2)

    if not words1 or not words2:
        return 0
    
    intersection = words1.intersection(words2)
    min_length = min(len(words1), len(words2))
    
    if min_length == 0:
        return 0

    return len(intersection) / min_length


def is_same_location(issue1, issue2):
    return ( issue1.building_id == issue2.building_id
             and issue1.floor_id == issue2.floor_id
             and issue1.room_id == issue2.room_id)


def is_duplicate(candidate_issue, existing_issue, threshold = 0.4):
    similarity = overlap_coefficient(candidate_issue.description, existing_issue.description)
    return similarity >= threshold


def find_duplicate(candidate_issue, existing_issue):
    for issue in existing_issue:
        if is_duplicate(candidate_issue, issue):
            return issue
    return None
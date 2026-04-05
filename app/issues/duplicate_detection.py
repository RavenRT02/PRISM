import re
from functools import lru_cache

STOPWORDS = { "the", "is", "in", "at", "on", "a", "an", "and",
    "or", "to", "for", "of", "with", "by", "from"}

@lru_cache(maxsize=1024)
def normalize(text):

    if not text:
        return set()
    
    words = re.sub(r"[^\w\s]", "", text.lower()).split()

    cleaned_words = { word for word in words if word not in STOPWORDS and len(word) > 2 }

    return cleaned_words


def jaccard_similarity(text1, text2):
    """compute similarity using jaccard index
        intersection / union"""
    
    words1 = normalize(text1)
    words2 = normalize(text2)

    if not words1 or not words2:
        return 0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def is_same_location(issue1, issue2):

    return ( issue1.building_id == issue2.building_id
             and issue1.floor_id == issue2.floor_id
             and issue1.room_id == issue2.room_id)


def is_duplicate(candidate_issue, existing_issue, threshold = 0.5):

    if not is_same_location(candidate_issue, existing_issue):
        return False
    
    similarity = jaccard_similarity(candidate_issue.description, existing_issue.description)

    return similarity >= threshold
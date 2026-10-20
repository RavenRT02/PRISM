import re
from functools import lru_cache
# from app.priority.priority_engine import clean_and_lemmatize


STOPWORDS = { "the", "is", "in", "at", "on", "a", "an", "and", "or", "to", "for", "of", "with", "by", "from" }

@lru_cache(maxsize=1024)
def normalize(text):
    pass


def overlap_coefficient(text1, text2):
    
    pass


def is_same_location(issue1, issue2):

    pass

def is_duplicate(candidate_issue, existing_issue, threshold = 0.4):

    pass


def find_duplicate(candidate_issue, existing_issue):

    pass
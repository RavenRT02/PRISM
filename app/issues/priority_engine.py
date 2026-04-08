from app.issues.enums import PriorityLevel, IssueStatus
from datetime import datetime, timezone
from app.utils.datetime_utils import ensure_utc
from app.issues.priority_keywords import URGENCY_KEYWORDS, IMPACT_KEYWORDS
import string
from spellchecker import SpellChecker
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

URGENCY_WEIGHT = 5
IMPACT_WEIGHT = 4
AGING_WEIGHT = 1

AGING_INCREMENT_DAYS = 3
AGING_SCORE_STEP = 2

PRIORITY_THRESHOLDS = [(PriorityLevel.CRITICAL, 80), (PriorityLevel.HIGH, 60), (PriorityLevel.MEDIUM, 40),]


def calculate_priority_score(issue):

    urgency = max(issue.urgency_score or 0, 0)
    impact = max(issue.impact_score or 0, 0)
    aging = max(issue.aging_score or 0, 0)

    return ( (urgency * URGENCY_WEIGHT) 
             + (impact * IMPACT_WEIGHT)
             + (aging * AGING_WEIGHT))


def assign_priority_level(score):

    for level, threshold in PRIORITY_THRESHOLDS:
        if score >= threshold:
            return level
    
    return PriorityLevel.LOW


def update_issue_priority(issue):

    auto_score_issue(issue)

    update_aging(issue)

    score = calculate_priority_score(issue)

    issue.priority_score = score
    issue.priority_level = assign_priority_level(score)

    return issue



def update_aging(issue):

    if not issue.approved_at:
        return
    
    now = ensure_utc(datetime.now(timezone.utc))
    
    days_elapsed = (now - issue.approved_at).days

    issue.aging_score = (days_elapsed // AGING_INCREMENT_DAYS) * AGING_SCORE_STEP


def check_hold_expiry(issue):

    if issue.status != IssueStatus.ON_HOLD:
        return False
    
    if not issue.hold_until:
        return False

    now = ensure_utc(datetime.now(timezone.utc))
    hold_until = ensure_utc(issue.hold_until)
    return now >= hold_until


def clean_and_lemmatize(description):
    
    description = description.lower().translate(str.maketrans("", "", string.punctuation))
    
    try:
        tokens = word_tokenize(description)
    except:
        tokens = description.split()
    
    spell = SpellChecker()
    misspelled = spell.unknown(tokens)
    corrected = []
    
    for token in tokens:
        if token in misspelled:
            correction = spell.correction(token)
            corrected.append(correction if correction else token)
        else:
            corrected.append(token)
            
    lemmatizer = WordNetLemmatizer()
    lemmas = [lemmatizer.lemmatize(word, pos='v') for word in corrected]
    lemmas = [lemmatizer.lemmatize(word, pos='n') for word in lemmas]
    
    return " ".join(lemmas)


def infer_urgency_score(cleaned_description):

    score = 0
    for category in URGENCY_KEYWORDS.values():
        if any(keyword in cleaned_description for keyword in category["keywords"]):
            score += category["score"]
    return score


def infer_impact_score(cleaned_description):

    score = 0
    for category in IMPACT_KEYWORDS.values():
        if any(keyword in cleaned_description for keyword in category["keywords"]):
            score += category["score"]
    return score


def auto_score_issue(issue):

    if not issue.description:
        issue.urgency_score = 0
        issue.impact_score = 0
        return issue

    cleaned_desc = clean_and_lemmatize(issue.description)

    issue.urgency_score = infer_urgency_score(cleaned_desc)
    issue.impact_score = infer_impact_score(cleaned_desc)

    return issue



from sklearn.metrics.pairwise import cosine_similarity
from app.similarity_search.reference_store import get_embedding_model


# similarity >= this score will be considered duplicate
DUPLICATE_THRESHOLD = 0.75


def is_duplicate(candidate_issue, existing_issue, threshold = DUPLICATE_THRESHOLD):
    """Return whether two issue descriptions are sufficiently similar"""

    candidate_description = (candidate_issue.description or "").strip()
    existing_description = (existing_issue.description or "").strip()

    if not candidate_description or not existing_description:
        return False

    model = get_embedding_model()
    embeddings = model.encode([candidate_description, existing_description])

    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

    return float(similarity) >= threshold



def find_duplicate(candidate_issue, existing_issue):
    """Return first active issue with sufficiently similar description"""

    for issue in existing_issue:
        if is_duplicate(candidate_issue=candidate_issue, existing_issue=issue):
            return issue

    return None
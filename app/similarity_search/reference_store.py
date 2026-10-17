import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Configuration
MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "issue_references"

DATASET_PATH = Path(__file__).resolve().parents[2] / "priority_dataset" / "processed_dataset.json"
CHROMA_PATH = Path(__file__).resolve().parents[2] / "instance" / "chroma_db"

# Load once when this module is imported.
embedding_model = SentenceTransformer(MODEL_NAME)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))

# metadata={"hnsw:space": "cosine"} for vector similary 
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME,metadata={"hnsw:space": "cosine"})


def load_reference_dataset():
    """Load the processed reference records from JSON."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def ingest_reference_dataset():
    """Insert the initial references into ChromaDB."""
    records = load_reference_dataset()

    if not records:
        return 0

    # .tolist() convert numpy array ( embeddings are in that format ) to normal python list
    collection.upsert(
        ids=[record["id"] for record in records],
        documents=[record["description"] for record in records],
        embeddings=embedding_model.encode([record["description"] for record in records]).tolist(),
        metadatas=[
            {
                "scope": record["scope"],
                "safety_min": record["safety_score_range"][0],
                "safety_max": record["safety_score_range"][1],
                "impact_min": record["impact_score_range"][0],
                "impact_max": record["impact_score_range"][1],
                "urgency_min": record["urgency_score_range"][0],
                "urgency_max": record["urgency_score_range"][1],
            }
            for record in records
        ],
    )

    return len(records)


def find_similar_references(description, n_results=3):
    """Retrieve the closest reference descriptions and their metadata."""
    if not description or not description.strip():
        return []

    query_embedding = embedding_model.encode([description.strip()]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    references = []

    for i, reference_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]

        references.append({
            "id": reference_id,
            "description": results["documents"][0][i],
            "scope": results["metadatas"][0][i]["scope"],
            "safety_score_range": [
                results["metadatas"][0][i]["safety_min"],
                results["metadatas"][0][i]["safety_max"],
            ],
            "impact_score_range": [
                results["metadatas"][0][i]["impact_min"],
                results["metadatas"][0][i]["impact_max"],
            ],
            "urgency_score_range": [
                results["metadatas"][0][i]["urgency_min"],
                results["metadatas"][0][i]["urgency_max"],
            ],
            "similarity": 1 - distance,
        })

    return references
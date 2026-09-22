# add sentence-transformers to requiremnts.txt after testing
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "priority_dataset" / "reference_dataset.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

with open(DATASET_PATH, "r", encoding="utf-8") as file:
    references = json.load(file)

descriptions = [
    reference["description"] 
    for reference in references
]

model = SentenceTransformer(EMBEDDING_MODEL)

embeddings = model.encode(descriptions, convert_to_tensor=True) 

# print("Number of reference examples:", len(descriptions))
# print("Embedding shape:", embeddings.shape)



def show_similar_examples(index, top_k = 5):

    query_embedding = embeddings[index]

    similarities = cos_sim(query_embedding, embeddings)[0]

    # Remove the example itself
    similarities[index] = -1

    top_results = similarities.argsort(descending=True)[:top_k]

    print("\n" + "=" * 80)
    print(f"QUERY — Example #{index + 1}")
    print(descriptions[index])
    print("=" * 80)

    for rank, result_index in enumerate(top_results, start=1):
        result_index = result_index.item()

        print(
            f"{rank}. "
            f"Example #{result_index + 1} "
            f"(similarity: {similarities[result_index]:.4f})"
        )
        print(f"   {descriptions[result_index]}")
        print()


# show_similar_examples(13)
# show_similar_examples(20)
# show_similar_examples(30)
# show_similar_examples(40)
# show_similar_examples(60)



def search_new_issue(query, top_k=5):

    query_embedding = model.encode(query, convert_to_tensor=True)

    similarities = cos_sim(query_embedding, embeddings)[0]

    top_results = similarities.argsort(descending=True)[:top_k]

    print("\n" + "=" * 80)
    print("NEW ISSUE")
    print(query)
    print("=" * 80)

    top_1 = similarities[top_results[0]]
    top_2 = similarities[top_results[1]]

    print(f"Top similarity: {top_1:.4f}")
    print(f"Second similarity: {top_2:.4f}")
    print(f"Gap: {top_1 - top_2:.4f}")

"""    for rank, result_index in enumerate(top_results, start=1):
        result_index = result_index.item()

        print(
            f"{rank}. "
            f"Example #{result_index + 1} "
            f"(similarity: {similarities[result_index]:.4f})"
        )


        reference = references[result_index]

        print(f"   {reference['description']}")
        print(f"   Safety:  {reference['safety_score_range']}")
        print(f"   Impact:  {reference['impact_score_range']}")
        print(f"   Urgency: {reference['urgency_score_range']}")
        print()"""


test_queries = [
    "The ceiling panel above the walkway is becoming loose and may fall.",
    "The main entrance to the building cannot be accessed.",
    "Several desks on the floor have damaged surfaces.",
    "Students cannot see anything from the classroom projector even though it is powered on.",
    "Liquid has spread across the laboratory floor after a container leaked.",
    "The corridor floor has become slippery because of water coming from the restroom.",
    "The classroom air conditioning has stopped working.",
    "The laboratory exhaust fan is no longer functioning.",
    "The first aid kits in the block need to be replenished.",
    "The laboratory ventilation system has stopped working during practical sessions."
]

for query in test_queries:
    search_new_issue(query)
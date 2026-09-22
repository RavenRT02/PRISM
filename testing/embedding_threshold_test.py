"""
PRISM - Held-out embedding threshold evaluation

Purpose:
    Evaluate whether the reference dataset contains a single reference that is
    strong enough to score a new issue directly, and identify where a fallback
    to the LLM should begin.

IMPORTANT:
    The expected labels below are HUMAN labels created before looking at the
    similarity results. They describe whether the existing reference dataset
    contains a directly reusable precedent for that issue.

    SUFFICIENT_REFERENCE
        A single reference example is close enough that its existing
        Safety/Impact/Urgency ranges could reasonably be reused directly.

    INSUFFICIENT_REFERENCE
        The dataset may contain related examples, but none should be trusted
        as a direct scoring precedent. This should eventually fall back to the
        LLM.

Do NOT change the expected labels after seeing the similarity results just to
make the thresholds look better. If a label is debatable, mark it in NOTES and
review it separately.
"""

import csv
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "priority_dataset" / "reference_dataset.json"
RESULTS_PATH = Path(__file__).resolve().parent / "embedding_threshold_results.csv"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


with open(DATASET_PATH, "r", encoding="utf-8") as file:
    references = json.load(file)

reference_descriptions = [reference["description"] for reference in references]

print(f"Loaded {len(references)} reference examples.")
print(f"Loading embedding model: {EMBEDDING_MODEL}")

model = SentenceTransformer(EMBEDDING_MODEL)
reference_embeddings = model.encode(reference_descriptions, convert_to_tensor=True)


# ---------------------------------------------------------------------------
# HELD-OUT TEST SET
# ---------------------------------------------------------------------------
# These are intentionally NOT copies of reference descriptions.
#
# Groups:
#   represented      = ordinary paraphrases of known issue types
#   contextual       = known issue types with a changed circumstance
#   borderline       = related to something in the dataset, but not a direct
#                      scoring precedent
#   novel            = issue type/context not adequately represented
#
# The expected label is based on whether ONE existing reference can be used
# directly for scoring, not whether the issue is merely related to something.
# ---------------------------------------------------------------------------

test_queries = [
    # -----------------------------------------------------------------------
    # 1. CLEARLY REPRESENTED - should have a directly reusable precedent
    # -----------------------------------------------------------------------
    {
        "id": "R01",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The desks in this classroom have minor scratches and surface marks.",
        "notes": "Desk surface damage is directly represented.",
    },
    {
        "id": "R02",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The classroom projector is powered on but is not displaying the lecture properly.",
        "notes": "Projector failure during class is directly represented.",
    },
    {
        "id": "R03",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The air conditioner in the classroom has stopped functioning.",
        "notes": "Classroom AC failure is directly represented.",
    },
    {
        "id": "R04",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "Several chairs in the room are damaged and need repairs.",
        "notes": "Classroom chair repair is directly represented.",
    },
    {
        "id": "R05",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "Most of the computers in the student laboratory cannot currently be used.",
        "notes": "Student lab computer availability is directly represented.",
    },
    {
        "id": "R06",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The restroom on this floor cannot be used at the moment.",
        "notes": "Restroom unavailable is directly represented.",
    },
    {
        "id": "R07",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "A ceiling tile is hanging loose above the classroom.",
        "notes": "Loose ceiling tile is directly represented.",
    },
    {
        "id": "R08",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The wheelchair ramp has a damaged walking surface.",
        "notes": "Damaged wheelchair ramp is directly represented.",
    },
    {
        "id": "R09",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "Water is leaking from the ceiling and reaching the floor.",
        "notes": "Ceiling water leak is directly represented.",
    },
    {
        "id": "R10",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "An electrical cable is exposed where students can reach it.",
        "notes": "Exposed accessible electrical wire is directly represented.",
    },
    {
        "id": "R11",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "There is no Wi-Fi service anywhere on this floor.",
        "notes": "Floor-wide Wi-Fi outage is directly represented.",
    },
    {
        "id": "R12",
        "group": "represented",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The whole building has lost its water supply.",
        "notes": "Building-wide water outage is directly represented.",
    },

    # -----------------------------------------------------------------------
    # 2. KNOWN ISSUE + DIFFERENT CONTEXT
    # -----------------------------------------------------------------------
    {
        "id": "C01",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The classroom projector has failed and an important university event is scheduled there tomorrow.",
        "notes": "Projector + urgent event context has a close precedent.",
    },
    {
        "id": "C02",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The main registration printer has stopped working and registration closes today.",
        "notes": "Registration printer + deadline context has a close precedent.",
    },
    {
        "id": "C03",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The auditorium microphone is unavailable for a university programme taking place tomorrow.",
        "notes": "Auditorium microphone + next-day function is directly represented.",
    },
    {
        "id": "C04",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The lecture hall AC is broken and an examination is scheduled in the hall tomorrow.",
        "notes": "Lecture hall AC + exam context is directly represented.",
    },
    {
        "id": "C05",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The campus Wi-Fi keeps disconnecting during an online examination today.",
        "notes": "Online exam + Wi-Fi issue is directly represented.",
    },
    {
        "id": "C06",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The wheelchair ramp is blocked and an event will use this area tomorrow.",
        "notes": "Blocked ramp + event context is directly represented.",
    },
    {
        "id": "C07",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The building fire alarm system is currently not operational.",
        "notes": "Fire alarm failure is directly represented.",
    },
    {
        "id": "C08",
        "group": "contextual",
        "expected": "SUFFICIENT_REFERENCE",
        "description": "The only accessible entrance to the building is currently blocked.",
        "notes": "Accessible entrance blockage is directly represented.",
    },

    # -----------------------------------------------------------------------
    # 3. BORDERLINE / RELATED BUT NOT DIRECTLY REUSABLE
    # -----------------------------------------------------------------------
    {
        "id": "B01",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The laboratory exhaust system has stopped working during practical sessions.",
        "notes": "There are laboratory safety examples, but no sufficiently direct exhaust-system precedent.",
    },
    {
        "id": "B02",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The laboratory fume hood is no longer extracting air properly.",
        "notes": "Related to laboratory ventilation but should not automatically inherit a chemical-spill score.",
    },
    {
        "id": "B03",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "A restroom sink is blocked and water drains very slowly.",
        "notes": "Restroom/water references exist, but this is a distinct minor plumbing failure.",
    },
    {
        "id": "B04",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "Most corridor lights on the floor are not functioning.",
        "notes": "Some room lights are represented, but this is a broader common-area lighting failure.",
    },
    {
        "id": "B05",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The only elevator serving the upper floors has stopped working and several classes are held there.",
        "notes": "An elevator failure exists, but the accessibility/sole-elevator context is materially different.",
    },
    {
        "id": "B06",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The classroom door handle is broken and the door cannot be secured properly.",
        "notes": "Door difficulty exists, but inability to secure the room introduces a different concern.",
    },
    {
        "id": "B07",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "Several laboratory refrigerators are not maintaining the required temperature.",
        "notes": "Laboratory equipment exists in the dataset, but this is a distinct equipment/storage problem.",
    },
    {
        "id": "B08",
        "group": "borderline",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The cafeteria food preparation sink has a persistent drainage problem.",
        "notes": "Food-area issues exist, but no direct plumbing reference exists for this situation.",
    },

    # -----------------------------------------------------------------------
    # 4. GENUINELY NOVEL / SHOULD FALL BACK TO LLM
    # -----------------------------------------------------------------------
    {
        "id": "N01",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The laboratory centrifuge is making unusual noises and cannot complete a cycle.",
        "notes": "Specific laboratory equipment failure is not represented.",
    },
    {
        "id": "N02",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The campus parking barrier is stuck open and vehicles are entering without authorization.",
        "notes": "Parking/security infrastructure is not represented.",
    },
    {
        "id": "N03",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The student ID card reader at the library entrance is rejecting valid cards.",
        "notes": "Access-control equipment is not directly represented.",
    },
    {
        "id": "N04",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The drinking-water dispenser is producing unusually hot water instead of chilled water.",
        "notes": "Water-dispenser availability requests exist, but this is a malfunction with a different scoring context.",
    },
    {
        "id": "N05",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The university shuttle tracking display is showing incorrect arrival times.",
        "notes": "Transportation service is not represented.",
    },
    {
        "id": "N06",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The online student portal is displaying incorrect examination-room assignments.",
        "notes": "Software/information-system error is not represented.",
    },
    {
        "id": "N07",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "The laboratory refrigerator containing temperature-sensitive samples has lost power.",
        "notes": "Specific laboratory storage failure is not represented.",
    },
    {
        "id": "N08",
        "group": "novel",
        "expected": "INSUFFICIENT_REFERENCE",
        "description": "A large branch has fallen onto the pedestrian path beside the academic block.",
        "notes": "Outdoor grounds hazard is not represented.",
    },
]


def search_issue(query, top_k=3):
    query_embedding = model.encode(query, convert_to_tensor=True)
    similarities = cos_sim(query_embedding, reference_embeddings)[0]
    top_results = similarities.argsort(descending=True)[:top_k]

    results = []
    for result_index in top_results:
        index = result_index.item()
        results.append(
            {
                "index": index + 1,
                "similarity": float(similarities[index]),
                "description": reference_descriptions[index],
                "safety": references[index]["safety_score_range"],
                "impact": references[index]["impact_score_range"],
                "urgency": references[index]["urgency_score_range"],
            }
        )

    return results


def print_result(test_case, results):
    top_1 = results[0]["similarity"]
    top_2 = results[1]["similarity"]
    gap = top_1 - top_2

    print("\n" + "=" * 100)
    print(f"{test_case['id']} | {test_case['group']}")
    print(f"Expected: {test_case['expected']}")
    print(f"Issue:    {test_case['description']}")
    print(f"Notes:    {test_case['notes']}")
    print("-" * 100)
    print(f"Top similarity:    {top_1:.4f}")
    print(f"Second similarity: {top_2:.4f}")
    print(f"Gap:               {gap:.4f}")
    print("\nTop 3 references:")

    for rank, result in enumerate(results, start=1):
        print(
            f"{rank}. #{result['index']} | similarity={result['similarity']:.4f}"
        )
        print(f"   {result['description']}")
        print(
            f"   Safety={result['safety']} | "
            f"Impact={result['impact']} | "
            f"Urgency={result['urgency']}"
        )


def main():
    results_for_csv = []

    for test_case in test_queries:
        results = search_issue(test_case["description"], top_k=3)
        print_result(test_case, results)

        top_1 = results[0]["similarity"]
        top_2 = results[1]["similarity"]

        row = {
            "id": test_case["id"],
            "group": test_case["group"],
            "expected": test_case["expected"],
            "description": test_case["description"],
            "top_similarity": round(top_1, 6),
            "second_similarity": round(top_2, 6),
            "gap": round(top_1 - top_2, 6),
            "top_reference_number": results[0]["index"],
            "top_reference": results[0]["description"],
            "second_reference_number": results[1]["index"],
            "second_reference": results[1]["description"],
            "third_reference_number": results[2]["index"],
            "third_reference": results[2]["description"],
            "notes": test_case["notes"],
        }
        results_for_csv.append(row)

    fieldnames = list(results_for_csv[0].keys())

    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results_for_csv)

    print("\n" + "=" * 100)
    print(f"Finished {len(test_queries)} held-out tests.")
    print(f"Results saved to: {RESULTS_PATH}")
    print("\nDo NOT choose thresholds from this output mechanically.")
    print("First inspect where SUFFICIENT_REFERENCE and INSUFFICIENT_REFERENCE cases overlap.")
    print("Then we can decide whether similarity alone is enough and whether the gap adds value.")


if __name__ == "__main__":
    main()


"""
Tested and fixed thresholds

similarity >= 0.70
    → direct reference scoring

0.55 <= similarity < 0.70
    → LLM + relevant top references

similarity < 0.55
    → LLM without references
"""
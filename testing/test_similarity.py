# Test 1
# Testing embedded data  -- uncomment / comment accordingly to run test
# Run with python -m testing.test_similarity

"""from app.similarity_search.reference_store import find_similar_references

test_descriptions = [
    # Test 1: Very close to a reference description
    "Scratch marks on the desk surface",

    # Test 2: Same general issue, different wording
    "The desk in the classroom has several scratches on its surface",
]

for description in test_descriptions:
    print(f"\nQuery: {description}")

    results = find_similar_references(description, n_results=3)

    for result in results:
        print(f"  ID: {result['id']}")
        print(f"  Description: {result['description']}")
        print(f"  Similarity: {result['similarity']:.4f}")
        print(f"  Safety range: {result['safety_score_range']}")
        print(f"  Impact range: {result['impact_score_range']}")
        print(f"  Urgency range: {result['urgency_score_range']}")"""



# Test 2
# Testing path logic -- uncomment / comment accordingly to run test
# Run with python -m testing.test_similarity

from app.priority.priority_engine import determine_priority_path

description = "Scratch marks on the desk surface"

decision = determine_priority_path(description)

print("Selected path:", decision["path"])
print("References:", decision["references"])



# Test 3 ( Needs to be run with test 2 )
# Testing assesment logic after getting path -- uncomment / comment accordingly to run test
# Run with python -m testing.test_similarity


from app.priority.priority_engine import calculate_from_reference

if decision["path"] == "reference":
    assessment = calculate_from_reference(
        decision["reference"]
    )

    print("Assessment:", assessment)
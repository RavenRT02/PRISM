# Test 1 -- Test llm assessment ( needs api key, model name and base url in env, url not required for openai models )
# run with -- python -m testing.test_llm_assessment

from app import create_app
from app.priority.llm_assessment import assess_issue_with_llm

app = create_app()

with app.app_context():
    assessment = assess_issue_with_llm(
        description=(
                    "Auditorium lacks first aid kits, school children who came for inspection fell and hurt their knee "
                    "from the broken tiles and we did not have first aid kits to treat them"
                    )
    )

    print("Assessment:", assessment)
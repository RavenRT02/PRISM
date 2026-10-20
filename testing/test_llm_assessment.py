# Test 1 -- Test llm assessment ( needs api key, model name and base url in env, url not required for openai models )
# run with -- python -m testing.test_llm_assessment

from app import create_app
from app.priority.llm_assessment import assess_issue_with_llm

app = create_app()

with app.app_context():
    assessment = assess_issue_with_llm(
        description=(
                    "A ceiling light fixture in the main library corridor is hanging partially loose from the ceiling, "
                    "and its electrical wiring is visible. The corridor is used by students throughout the day, "
                    "and people have to walk directly underneath the fixture to reach the study areas."
                    )
    )

    print("Assessment:", assessment)
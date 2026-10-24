# Evaluation Framework: Recipe AI Application

Systematic evaluation is essential for assessing whether our recipe application reliably solves the user's problem, focusing specifically on retrieval accuracy, system resilience, and dietary safety.

## Evaluation Strategy

Our evaluation methodology tests both the AI components (local RAG fallback) and the deterministic safety mechanisms (dietary filters). The test cases are defined in [`test_cases.json`](test_cases.json).

### Test Case Categories

Our evaluation dataset covers four primary categories:

1. **RAG Success (Typical Inputs):** Standard ingredient queries to verify that the local fallback RAG correctly vectorizes and matches relevant recipes using cosine similarity.
2. **RAG Constraints / Difficult Cases:** Out-of-domain or unusual ingredients (e.g., "dragonfruit", "truffle oil") to ensure the system degrades gracefully and returns empty results instead of hallucinating.
3. **Dietary Filtering (Safety Checks):** Queries combining conflicting ingredients and dietary preferences (e.g., searching for "butter" and "milk" with a "dairy-free" preference) to verify the 100% accuracy of our deterministic rule-based filter.
4. **Fallback Simulation:** System behavior tests to verify that the application smoothly transitions to the local RAG database when the primary external Recipe API fails or drops the connection.

## Evaluation Process

1. **Define Test Cases:** Realistic user scenarios and expected behaviors are mapped out in `test_cases.json`.
2. **Execute System:** Each scenario is run through the `RecipeService` pipeline, testing both retrieval and filtering logic.
3. **Log & Review:** The actual results are recorded and assigned a status (`pass`, `fail`, `partial`).
4. **Summarize Results:** Findings, pass rates, identified limitations (such as language barriers in offline data), and future action items are documented in [`evaluation_results.md`](evaluation_results.md).
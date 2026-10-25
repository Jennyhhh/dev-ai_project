
User
  |
  v
Gradio UI (app/ui.py)
  |
  +---> Recipe Service (src/services/recipe_service.py)
  |       |
  |       +---> Recipe API Client (src/clients/recipe_api_client.py)
  |       |         |
  |       |         +---> TheMealDB API (internet)
  |       |
  |       +---> Local Recipe Retrieval (RAG)
  |                 |
  |                 +---> Local Recipe Dataset
  |
  +---> AI Service (src/services/ai_service.py)
  |       |
  |       +---> Prompts (src/services/prompts.py)
  |       |
  |       +---> Response Schemas (src/schemas/responses.py)
  |       |
  |       +---> Model Client (src/models/model_client.py)
  |                 |
  |                 +---> Ollama (local)
  |                           |
  |                           +---> Llama 3.2
  |
  +---> Memory (src/capabilities/memory.py)
            |
            +---> User Preferences (data/user_preferences.json)

## Components

| Component | File | What it does |
|---|---|---|
| User interface | `app/ui.py` | Gradio page: ingredient input, diet, pantry staples, recipe cards, AI recommendations and chat. Shows data and passes user input to the other layers. |
| Memory | `src/capabilities/memory.py` | Saves and loads the user's diet and pantry staples in a JSON file. Removes pantry staples from missing ingredients. |
| Recipe service | `src/services/recipe_service.py` | Searches recipes for each ingredient, compares ingredients and sorts the results by how well they match. |
| Recipe API client | `src/clients/recipe_api_client.py` | Makes the HTTP requests to TheMealDB. |
| AI service | `src/services/ai_service.py` | Builds the request to the model, checks the answer and handles errors. Also handles the follow-up chat. |
| Prompts | `src/services/prompts.py` | All instructions for the recommendation model in one place. |
| Schemas | `src/schemas/responses.py` | Pydantic models that define what a valid AI answer looks like. |
| Model client | `src/models/model_client.py` | Sends requests to the local Ollama server. |

## Why it is built this way

- **The UI does not talk to the model directly.** All AI requests go through the AI service. This
  way the prompt, validation and error handling are in one place and can be tested without the UI.
- **Facts come from code, the model only chooses and explains.** Recipe search and ingredient
  matching are done in normal code, because they must be correct. The model is only used for the
  part where language skills help: choosing the best recipes and explaining why.
- **Prompts are in their own file.** It is easy to find and change the instructions without
  touching the logic.
- **Memory is a separate module.** Saving and loading preferences does not depend on the UI or
  the model.

## Failure handling

| Situation | What happens |
|---|---|
| The model returns invalid JSON | The answer is retried once. If it fails again, the recipes are still shown and the user is told that AI recommendations are not available. |
| The model recommends a recipe that was not found, or the same recipe twice | The recipe is removed in code and a warning is logged. |
| Ollama is not running | Recipes are still shown; AI recommendations and chat show an error message. |
| TheMealDB does not respond | Requests time out after 10 seconds. Failed searches are skipped, so the user may see "no recipes found" instead of a network error (known limitation). |
| The memory file is missing or broken | Default preferences are used and a warning is logged. The app does not crash. |

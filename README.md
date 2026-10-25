What Should I Cook Today?

## Team members

- Member 1 Jenny Heikkilä (jenny.heikkila@student.hamk.fi) github: Jennyhhh
- Member 2 Saija Joronen (saija21006@student.hamk.fi) github: soijj98
- Member 3 Joona Peltola (joona23005@student.hamk.fi) github: joonaleksanteri

## Presentation Video
[[Link to our final project presentation video] ](https://youtu.be/TdNVBuheZCY)

## Problem

### Intended users
People who lacks time or ideas of making food for everyday. Also people who want's some change to their weekly cooking.

### Problem statement
Saves time and adds variety to cooking.

### Why AI is appropriate
because it can quickly search for many different recipes at the same time using the specified ingredients, and tell you if you dont have some ingredient what you need.

## Solution

An AI-powered recipe application that suggests recipes based on available ingredients, dietary preferences, and user needs.

The application includes a Gradio interface for ingredient-based recipe searching, recipe cards, dietary filtering, and an AI chatbot powered by Llama 3.2 through Ollama.

Users can ask cooking-related questions, select a recipe for more specific assistance, or chat with the AI without selecting a recipe.

## Main user workflow

1. **Gradio User Interface:** The user interacts with the application through a custom Gradio interface, which includes ingredient input fields, dietary preferences, recipe cards, recipe selection, and an AI chatbot.
2. **Recipe Search:** The user enters available ingredients, and the recipe service searches for matching recipes using TheMealDB API.
3. **Processing & Guardrails:** The application processes ingredient matches and validates recipe information.
4. **TheMealDB API Integration:** The recipe service communicates with TheMealDB through src/clients/recipe_api_client.py to retrieve recipes, including ingredients, instructions, and images.
5. **RAG Fallback:** If the API fails, the service retrieves recipes locally from the RAG database using embeddings/keyword matching.
6. **Dietary Filtering:** A deterministic filter removes recipes containing ingredients that violate the user's dietary preferences.
7. **Recipe Results:** Matching recipes are displayed in the Gradio interface as recipe cards with relevant information.
8. **Optional Recipe Selection:** The user can select a recipe to provide context for the AI chatbot. Selecting a recipe is not required.
9. **AI Chatbot:** The user can ask questions about cooking, ingredients, or selected recipes. The chatbot uses conversation history to support follow-up questions.
10. **Model Response:** The AI service communicates with the local Llama 3.2 model through Ollama and returns the generated response to the Gradio interface.
    
## Architecture

Below is the initial starter architecture. As your project evolves with additional capabilities, replace or extend this diagram in [`docs/architecture.md`](docs/architecture.md).

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ↓
Model Client (src/models/model_client.py)
  ↓
Ollama (Local LLM Server)
```

> **Core Architectural Rule:** The user interface must NEVER communicate directly with the model client or Ollama. All interactions must pass through the service layer (`ai_service.py`).

## Model

- **Model used:** e.g., `llama3.2` (or specified local Ollama model)
- **Selection rationale:** Why was this specific model chosen for your project (e.g., lightweight, performance, context size)?
- We chose llama3.2 as our starting model because it is lightweight enough to run on all team members' laptops, requires no API keys or
  usage costs, and keeps user data on the local machine. Can be changed later if we see it necessary.

## Reliable model interaction

The AI can only recommend recipes that the app has really found. This is done in five ways:

- **Clear instructions** (`src/services/prompts.py`): the AI gets the user's ingredients, diet and
  the found recipes. It is told to choose only from these recipes. It must not invent recipes,
  ingredients or cooking times.
- **Fixed answer format:** the AI must answer in JSON with a fixed structure
  (`src/schemas/responses.py`). Ollama makes sure the answer follows this structure.
- **Answer check and retry:** the app checks the answer with Pydantic. If the answer is broken,
  the AI gets one more try. If it fails again, the recipes are still shown, but without
  AI recommendations.
- **Wrong recipes removed:** if the AI recommends a recipe that was not found, or the same
  recipe twice, the app removes it and writes a warning to the log.
- **Facts from code:** the app itself calculates which of the user's ingredients a recipe uses.
  This is shown next to each recommendation. The AI only writes the reason.

We use English for the AI, because in our tests llama3.2 made mistakes in Finnish and invented
things, like cooking times. In English it followed the instructions better.

## AI Chatbot features

The AI chatbot was updated to support more flexible interaction with users.
General conversation: Users can communicate with the AI assistant without selecting a recipe.
Optional recipe context: When a recipe is selected, its information can be provided to the AI for more specific assistance.
Conversation history: Previous messages are included in the chatbot context to support follow-up questions.
Cooking assistance: The chatbot can answer questions about recipes, ingredients, and cooking methods.
Error handling: The application handles model communication errors and displays feedback to the user.
The chatbot communicates with Ollama through the AI service layer.
Updated files:
app/ui.py
src/services/ai_service.py
src/services/prompts.py
src/models/model_client.py

## Additional AI capability

Select at least one additional capability to implement for your final project:

- [x] RAG (Retrieval-Augmented Generation)
- [x] Tools / External API integration
- [ ] Model Context Protocol (MCP)
- [ ] Agentic workflow (Model-selected actions based on observations)
- [x] Memory / Persistent state
- [ ] Multimodal interaction (Text + Images)
- [ ] Other: ______________________

### Capability justification
Memory, so the application remembers all your favorites, disliked foods, preferences and dietary.
Tools, so we can get as many recipes to be used, from internet.
RAG, if we can't get API as example to work or we want the application to work offline.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dev-ai-project
```

### 3. Configure environment variables

Copy `.env.example` to create your local `.env` configuration file:

On Linux / macOS:
```bash
cp .env.example .env
```

On Windows (Command Prompt / PowerShell):
```powershell
copy .env.example .env
```

Ensure `.env` contains valid values for `OLLAMA_BASE_URL` and `MODEL_NAME`:
```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.2
```

### 4. Start Ollama

Make sure Ollama is installed and running locally, then pull your configured model:

```bash
ollama run llama3.2
```

### 5. Run the application

Run the application from the root directory of the project:

```bash
python -m app.main
```

Then open your browser at `http://localhost:7860`.

### 6. Run automated tests

```bash
pytest
```
### 7. Prepare local RAG data
To use the offline fallback search, generate the recipe JSON from the raw Kaggle dataset:
```bash
python convert_recipes.py
```

## Evaluation

The system's RAG fallback and deterministic dietary filtering were evaluated using specific test cases (successful search, difficult constraints, allergen filtering, and API failure simulation). 
- **Pass Rate:** 100% (4/4 test cases passed).
- The dietary filter correctly identified and removed recipes containing dairy and gluten when required.
Full evaluation details and failure analysis can be found in [`evaluation/evaluation_results_summary.md`](evaluation/evaluation_results_summary.md).

### UI, API and Chatbot Integration Testing (Joona)

The Gradio user interface, TheMealDB API integration, recipe search functionality, and AI chatbot were manually tested during development.
The purpose of these tests was to verify that the different application components work together correctly and that users can search for recipes and interact with the AI assistant.

| # | Test case | Expected result | Result |
|---|---|---|---|
| 1 | Application startup | Gradio application starts successfully | Pass |
| 2 | TheMealDB API search | Recipes are retrieved from the external API | Pass |
| 3 | Dietary filtering | Vegan, Vegetarian, and Gluten-free filters work correctly in tested cases | Pass |
| 4 | Local RAG fallback | Recipes can be retrieved from local data when needed | Pass |
| 5 | AI chatbot with Llama 3.2 | Chatbot responds to user questions | Pass |
| 6 | Conversation history | Chatbot uses previous messages as context | Pass |
| 7 | Optional recipe selection | Chatbot works with and without a selected recipe | Pass |
| 8 | Persistent preferences end-to-end test | Preferences remain available after restarting the application | Not fully tested |

**Testing summary:**

The application successfully started, retrieved recipes through TheMealDB, applied dietary filtering in tested cases, and supported local RAG retrieval.
The Llama 3.2 chatbot was tested with selected recipe context, without a selected recipe, and with conversation history. All these interactions worked during manual testing.
The complete end-to-end testing of persistent preferences was not finished as part of this testing round.

### AI recommendations and memory (manual tests)

We tested the AI recommendations and memory by hand during development. The AI answers are
written text and change a little every time, so a person must read them to check if they are
correct. Every problem we found led to a fix.

| # | Input | Expected | Result at the time | Action taken |
|---|---|---|---|---|
| 1 | First prompt, `chicken, pasta` | Correct recommendation | fail: bad Finnish, invented cooking time | New prompt in English; AI may only choose found recipes |
| 2 | New prompt, `chicken, pasta` | Only found recipes, no cooking times | pass | - |
| 3 | `chicken, pasta, tomato` | Correct reasons | partial: reasons sometimes named wrong ingredients | Used ingredients are now calculated in code |
| 4 | `chicken, pasta, tomato`, vegan | No chicken recipes | fail: AI recommended chicken | Dietary filter added in code |
| 5 | `chicken, pasta`, vegetarian | No duplicates | fail: same recipe three times | Duplicates are removed in code |
| 6 | Pantry staples include `garlic` | Garlic not shown as missing | pass | - |
| 7 | Restart the app | Diet and pantry staples remembered | pass | - |
| 8 | Broken preferences file | Default settings, no crash | pass | - |

**What we learned:** a small AI model does not always follow rules. Important rules, like diets
and allergies, must be checked in code, not only told to the AI.

## Known limitations

- **Language Barrier in RAG:** The current local dataset (`recipes.json`) uses English recipes. If a user inputs ingredients in Finnish (e.g., "omena"), the basic RAG search might fail to match them correctly without a multilingual embedding model or a translation step before retrieval.

## Future improvements

- **Macronutrient Goals & Tracking:** Introduce the ability for users to specify desired macros (e.g., protein, carbs, fats, calories) alongside their ingredients. The system would filter or prioritize recipes that align with the user's specific nutritional targets, providing a powerful tool for fitness and health-conscious users.
- **Multilingual Support for RAG:** Implement an automatic translation layer before the RAG retrieval. This would allow users to search with Finnish ingredients (e.g., "omena", "kana") and still successfully match against the English local offline recipe database.
- **Automated E2E Testing:** Expand the testing suite to include comprehensive, automated end-to-end (E2E) testing for persistent user preferences and UI interactions to ensure consistent behavior across sessions.
- **Enhanced Recipe Extraction API:** Integrate a more advanced web-scraping or API tool to pull in a wider variety of recipes dynamically from the internet, expanding the meal options beyond the current sources.

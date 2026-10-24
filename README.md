# Project name

Starter template for the **Development of AI Applications** course final group project.

## Team members

- Member 1 Jenny Heikkilä (jenny.heikkila@student.hamk.fi) github: Jennyhhh
- Member 2 Saija Joronen (saija21006@student.hamk.fi) github: soijj98
- Member 3 Joona Peltola (joona23005@student.hamk.fi) github: joonaleksanteri

## Presentation Video
[Link to our final project presentation video] 

## Problem

### Intended users
People who lacks time or ideas of making food for everyday. Also people who want's some change to their weekly cooking.

### Problem statement
Saves time and adds variety to cooking.

### Why AI is appropriate
because it can quickly search for many different recipes at the same time using the specified ingredients, and tell you if you dont have some ingredient what you need.

## Solution

An AI-powered recipe app that suggests recipes based on the ingredients, preferences, and dietary needs you provide.

## Main user workflow

1. **User Input:** The user submits a prompt or query via the Gradio user interface.
2. **Processing & Guardrails:** The application service layer (`src/services/ai_service.py`) validates and formats the request.
3. **RAG Fallback:** If the API fails, the service retrieves recipes locally from the RAG database using embeddings/keyword matching.
4. **Dietary Filtering:** A deterministic filter removes any recipes containing ingredients that violate the user's dietary preferences (e.g., dairy, gluten, meat).
5. **Model Response:** The model client calls Ollama locally and returns the response back through the service layer to the UI.

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

## Known limitations

- **Language Barrier in RAG:** The current local dataset (`recipes.json`) uses English recipes. If a user inputs ingredients in Finnish (e.g., "omena"), the basic RAG search might fail to match them correctly without a multilingual embedding model or a translation step before retrieval.

## Future improvements

- List planned feature enhancements, architectural refactorings, or future capabilities.

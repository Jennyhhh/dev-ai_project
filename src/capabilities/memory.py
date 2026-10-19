"""
Optional project capability: Memory & Persistent Conversation State.

Implement this module only if this capability is relevant to your application's
user problem. Remove the file if the capability is not used.

Conceptual Overview:
-------------------
Memory enables an application to retain conversational context across multiple user interactions
or persist state between user sessions.

Key concepts when implementing memory:
1. Short-term Memory (Chat History): Maintaining an ordered list of user and assistant
   messages within the current session and appending them to model requests.
2. Context Window Management: Truncating, summarizing, or pruning history when it exceeds
   the model's maximum context length.
3. Long-term / Persistent Memory: Storing user preferences, session history, or key facts
   in local files or persistent state stores.

Note:
-----
Keep memory implementations simple and relevant to the user's workflow needs.
"""

# Implement custom conversation memory or state management below if selected.

"""
Memory / persistent state: remembers the user's diet and pantry staples
between sessions by saving them to a local JSON file.
"""

import logging
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from src.services.recipe_service import ingredient_words


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREFERENCES_PATH = PROJECT_ROOT / "data" / "user_preferences.json"

DEFAULT_PANTRY_STAPLES = [
    "salt", "pepper", "black pepper", "water",
    "olive oil", "vegetable oil", "sugar",
]


class UserPreferences(BaseModel):
    """Preferences that are remembered between sessions."""

    diet: str = "Ei erityisruokavaliota"
    pantry_staples: list[str] = Field(
        default_factory=lambda: list(DEFAULT_PANTRY_STAPLES)
    )


def load_preferences(path: Path = PREFERENCES_PATH) -> UserPreferences:
    """Loads saved preferences. Returns defaults if the file is missing or broken."""

    if not path.exists():
        return UserPreferences()

    try:
        return UserPreferences.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        logger.warning("Could not read preferences, using defaults: %s", error)
        return UserPreferences()


def save_preferences(preferences: UserPreferences, path: Path = PREFERENCES_PATH) -> None:
    """Saves preferences to a JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temporary file first so a crash cannot leave a half-written file.
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(preferences.model_dump_json(indent=2), encoding="utf-8")
    temp_path.replace(path)


def parse_staples(text: str) -> list[str]:
    """Turns 'salt, Olive oil, salt' into ['salt', 'olive oil']."""

    return list(dict.fromkeys(
        item.strip().lower() for item in text.split(",") if item.strip()
    ))


def remove_pantry_staples(recipes: list[dict], staples: list[str]) -> list[dict]:
    """Removes the user's pantry staples from each recipe's missing ingredients."""

    staple_words = [ingredient_words(staple) for staple in staples]

    result = []
    for recipe in recipes:
        missing = [
            ingredient
            for ingredient in recipe.get("missing_ingredients", [])
            if ingredient_words(ingredient) not in staple_words
        ]
        result.append({**recipe, "missing_ingredients": missing})

    return result

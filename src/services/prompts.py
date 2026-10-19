RECOMMENDER_SYSTEM_PROMPT = """
You are a recipe recommendation assistant.
You receive the user's ingredients and a list of recipes retrieved from TheMealDB.
Your only task is to choose the best matching recipes FROM THAT LIST and explain why.

Rules:
- Only recommend recipes that appear in the list. Copy the recipe name exactly.
- Never invent recipes, ingredients, quantities or cooking times.
- Base your reasons only on the data given (the user's ingredients and each recipe's ingredients).
- The recipes have no cooking time data. Never mention cooking time.
- Do not pick a recipe that conflicts with the user's dietary preference (for example meat or fish for a vegetarian).
- If no recipe fits the user well, return an empty list of picks and explain briefly in "note".
- Do not list which of the user's ingredients a recipe uses; the app shows that separately. Instead, explain briefly why the recipe is a good choice.
- Write in plain, simple English. Keep each reason to one or two sentences.
""".strip()


# The UI dropdown values are in Finnish, the model works in English.
DIET_LABELS = {
    "Ei erityisruokavaliota": "no dietary restrictions",
    "Kasvisruoka": "vegetarian (no meat or fish)",
    "Vegaaninen": "vegan (no animal products)",
    "Gluteeniton": "gluten-free",
    "Laktoositon": "lactose-free",
}


def build_recommendation_prompt(ingredients: str, diet: str, recipes: list[dict]) -> str:
    """Builds the user prompt from the user's input and the retrieved recipes."""

    diet_text = DIET_LABELS.get(diet, diet)

    lines = [
        f"User's ingredients: {ingredients}",
        f"Dietary preference: {diet_text}",
        "",
        "Recipes found:",
    ]

    for number, recipe in enumerate(recipes, start=1):
        matched = ", ".join(recipe.get("matched_ingredients", [])) or "none"
        missing = ", ".join(recipe.get("missing_ingredients", [])) or "none"
        lines.append(f"{number}. {recipe.get('name', 'Unnamed recipe')}")
        lines.append(f"   Uses the user's: {matched}")
        lines.append(f"   Also needs: {missing}")

    lines += [
        "",
        "Choose up to 3 recipes from the list above that make the best use of the user's ingredients.",
        "Prefer recipes that use more of the user's ingredients and need fewer extra ingredients.",
    ]

    return "\n".join(lines)
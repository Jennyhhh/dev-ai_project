
import re

from src.clients.recipe_api_client import (
    search_recipes_by_ingredient,
    get_recipe_details,
)


def normalize_ingredient(value: str) -> str:
    """Yhtenäistää englanninkielisen ainesosan vertailua varten."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return " ".join(value.split())


def singularize_word(word: str) -> str:
    """Käsittelee tavallisimmat englannin monikkomuodot."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"

    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]

    return word


def ingredient_words(value: str) -> list[str]:
    """Muuttaa ainesosan vertailukelpoisiksi sanoiksi."""
    return [
        singularize_word(word)
        for word in normalize_ingredient(value).split()
    ]


def ingredient_matches(
    user_ingredient: str,
    recipe_ingredient: str,
) -> bool:
    """Vertaa ainesosia joustavasti ilman mielivaltaisia osumia."""
    user_words = ingredient_words(user_ingredient)
    recipe_words = ingredient_words(recipe_ingredient)

    if not user_words or not recipe_words:
        return False

    if user_words == recipe_words:
        return True

    if len(user_words) == 1 and user_words[0] in recipe_words:
        return True

    if len(recipe_words) == 1 and recipe_words[0] in user_words:
        return True

    return False


def clean_recipe_name(name: str) -> str:
    """Siistii reseptin nimen ylimääräisistä välilyönneistä."""
    name = re.sub(r"\s+", " ", name)
    return name.strip(" -,:;")


def get_recipe_ingredients(details: dict) -> list[str]:
    """Kerää reseptin ainesosat alkuperäisessä muodossa."""
    ingredients = []

    for index in range(1, 21):
        value = details.get(f"strIngredient{index}")

        if isinstance(value, str) and value.strip():
            ingredients.append(value.strip())

    return ingredients


def search_recipes(ingredients_text: str) -> list[dict]:
    """Hakee reseptejä, vertailee ainesosia ja järjestää tulokset."""

    ingredients = list(dict.fromkeys(
        normalize_ingredient(item)
        for item in ingredients_text.split(",")
        if item.strip()
    ))

    if not ingredients:
        return []

    candidate_scores = {}

    for ingredient in ingredients:
        try:
            recipes = search_recipes_by_ingredient(ingredient)
        except Exception:
            continue

        for recipe in recipes or []:
            recipe_id = recipe.get("idMeal")

            if not recipe_id:
                continue

            candidate_scores[recipe_id] = (
                candidate_scores.get(recipe_id, 0) + 1
            )

    candidate_ids = sorted(
        candidate_scores,
        key=lambda recipe_id: candidate_scores[recipe_id],
        reverse=True,
    )[:40]

    results = []

    for recipe_id in candidate_ids:
        try:
            details = get_recipe_details(recipe_id)
        except Exception:
            continue

        if not details:
            continue

        original_ingredients = get_recipe_ingredients(details)

        matched = [
            ingredient
            for ingredient in ingredients
            if any(
                ingredient_matches(ingredient, recipe_ingredient)
                for recipe_ingredient in original_ingredients
            )
        ]

        missing = [
            ingredient
            for ingredient in original_ingredients
            if not any(
                ingredient_matches(user_ingredient, ingredient)
                for user_ingredient in ingredients
            )
        ]

        original_name = clean_recipe_name(
            details.get("strMeal") or "Nimetön resepti"
        )

        original_instructions = (
            details.get("strInstructions") or ""
        ).strip()

        results.append({
            "id": recipe_id,
            "name": original_name,
            "image": details.get("strMealThumb") or "",
            "instructions": original_instructions,
            "ingredients": original_ingredients,
            "matched_ingredients": matched,
            "missing_ingredients": missing,
            "match_count": len(matched),
            "total_user_ingredients": len(ingredients),
        })

    results.sort(
        key=lambda recipe: (
            -recipe["match_count"],
            len(recipe["missing_ingredients"]),
            recipe["name"].lower(),
        )
    )

    return results
